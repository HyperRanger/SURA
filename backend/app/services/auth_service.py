"""Signup, login and one-time-code verification.

The role is decided here and only here. Signup cannot be talked into a different
role by the request body, the code is issued by the server rather than supplied by
the client, and the issued token carries the role so protected endpoints can
re-check it. A challenge is single-use, time-limited and attempt-capped.
"""

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AuthChallenge, SessionRevocation, TrustedDevice, User, Vendor
from app.services.sms import SmsDeliveryError, send_otp
from core.config import get_settings
from core.passwords import PasswordTooLong, hash_password, verify_password
from core.security import (
    create_token,
    generate_otp,
    hash_otp,
    new_otp_salt,
    otp_matches,
)

logger = logging.getLogger(__name__)

INDIVIDUAL_ROLE = "individual"
VENDOR_ROLE = "vendor"
BANK_ROLE = "bank"
ADMIN_ROLE = "admin"

ASSIGNABLE_ROLES = {INDIVIDUAL_ROLE, VENDOR_ROLE}

PURPOSE_SIGNUP = "signup"
PURPOSE_LOGIN = "login"
PURPOSE_BANK_MFA = "bank_mfa"

TRUSTED_DEVICE_DAYS = 5
GENERIC_CREDENTIALS_ERROR = "Email, phone number, or password is incorrect."
# Keeps an unknown identifier on the same bcrypt-cost path as a wrong password.
_DECOY_PASSWORD_HASH = hash_password("sura-member-login-decoy")


NIGERIA_COUNTRY_CODE = "234"


def normalize_phone(phone: str) -> str:
    """Store one canonical form per person.

    A Nigerian user typing 08030000012 and one typing +234 803 000 0012 are the
    same person, so the local form is rewritten to the international one.
    Comparing only digits is not enough: without this, the two formats produce
    two different accounts and the second one can never log in to the first.
    """
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) < 7:
        raise HTTPException(status_code=400, detail="Enter a valid phone number.")
    if digits.startswith("0"):
        digits = NIGERIA_COUNTRY_CODE + digits[1:]
    return digits


def _get_by_phone(db: Session, phone: str) -> User | None:
    return db.execute(select(User).where(User.phone == phone)).scalars().first()


def _normalise_email(email: str) -> str:
    candidate = email.strip().lower()
    if "@" not in candidate or candidate.startswith("@") or candidate.endswith("@"):
        raise HTTPException(status_code=400, detail="Enter a valid email address.")
    return candidate


def _get_by_identifier(db: Session, identifier: str) -> User | None:
    candidate = identifier.strip()
    if "@" in candidate:
        return db.execute(select(User).where(func.lower(User.email) == candidate.lower())).scalars().first()
    return _get_by_phone(db, normalize_phone(candidate))


def _device_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _issue_trusted_device(db: Session, user: User) -> str:
    """Replace any presented device credential with a fresh five-day secret."""
    raw_token = secrets.token_urlsafe(32)
    now = datetime.utcnow()
    db.add(
        TrustedDevice(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=_device_token_hash(raw_token),
            created_at=now,
            last_used_at=now,
            expires_at=now + timedelta(days=TRUSTED_DEVICE_DAYS),
        )
    )
    return raw_token


def _has_valid_trusted_device(db: Session, user: User, token: str | None) -> bool:
    if not token:
        return False
    device = (
        db.execute(select(TrustedDevice).where(TrustedDevice.token_hash == _device_token_hash(token)))
        .scalars()
        .first()
    )
    now = datetime.utcnow()
    if device is None or device.user_id != user.id or device.revoked_at is not None or device.expires_at <= now:
        return False
    device.last_used_at = now
    # A use does not slide the expiry: OTP is required again after five days.
    db.commit()
    return True


def revoke_trusted_devices(db: Session, user_id: str) -> int:
    """Make every remembered browser step up with OTP on its next login."""
    now = datetime.utcnow()
    changed = (
        db.query(TrustedDevice)
        .filter(TrustedDevice.user_id == user_id, TrustedDevice.revoked_at.is_(None))
        .update({TrustedDevice.revoked_at: now}, synchronize_session=False)
    )
    return int(changed)


def _issue_challenge(
    db: Session,
    user: User,
    purpose: str,
    deliver_to: str | None = None,
    background_tasks: BackgroundTasks | None = None,
) -> tuple[AuthChallenge, str]:
    """Create a pending challenge, returning it with the plaintext code.

    The code is returned for the SMS gateway to send. It is never persisted: only
    its salted hash goes to the database, so the row is useless on its own.
    """
    settings = get_settings()
    now = datetime.utcnow()

    # The cooldown and the supersede are per user, not per purpose, so a caller
    # cannot dodge the resend timer by asking for a login code straight after a
    # signup code. It is also what stops two live codes existing for one account.
    pending = (
        db.execute(
            select(AuthChallenge)
            .where(AuthChallenge.user_id == user.id, AuthChallenge.consumed_at.is_(None))
            .order_by(AuthChallenge.created_at.desc())
        )
        .scalars()
        .all()
    )

    if pending:
        most_recent = pending[0]
        if most_recent.created_at is not None:
            cooldown_until = most_recent.created_at + timedelta(
                seconds=settings.otp_resend_cooldown_seconds
            )
            if now < cooldown_until:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Wait {settings.otp_resend_cooldown_seconds}s before requesting another code.",
                )
        for stale in pending:
            stale.consumed_at = now

    code = generate_otp()
    salt = new_otp_salt()
    challenge = AuthChallenge(
        id=str(uuid.uuid4()),
        user_id=user.id,
        purpose=purpose,
        code_hash=hash_otp(code, salt),
        salt=salt,
        attempts=0,
        created_at=now,
        expires_at=now + timedelta(seconds=settings.otp_ttl_seconds),
    )
    db.add(challenge)
    db.commit()
    destination = deliver_to or user.phone
    if background_tasks is None:
        _deliver(challenge.id, destination, code)
    else:
        # The challenge is committed before this task is queued.  The client
        # can move to its verification screen without waiting for an SMS HTTP
        # request, while the resend cooldown still protects the provider.
        background_tasks.add_task(_deliver, challenge.id, destination, code)
    return challenge, code


def issue_otp_challenge(
    db: Session, user: User, purpose: str, deliver_to: str | None = None
) -> tuple[AuthChallenge, str]:
    """Public entry point for other domains that verify a code by SMS.

    Bank staff use it to prove possession of a second factor. `deliver_to` exists
    because that is not always the account's phone number.
    """
    return _issue_challenge(db, user, purpose, deliver_to=deliver_to)


def resend_otp(db: Session, challenge_id: str, background_tasks: BackgroundTasks | None = None) -> dict[str, Any]:
    """Replace one pending member-auth code without repeating credentials.

    The existing challenge identifies a pending authentication attempt.  Its
    normal cooldown and single-live-code rules still run in ``_issue_challenge``.
    """
    previous = db.get(AuthChallenge, challenge_id)
    if previous is None or previous.consumed_at is not None or previous.purpose not in {PURPOSE_SIGNUP, PURPOSE_LOGIN}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request a new sign-in code.")
    user = db.get(User, previous.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request a new sign-in code.")
    challenge, code = _issue_challenge(db, user, previous.purpose, background_tasks=background_tasks)
    return _challenge_response(challenge, code, get_settings().otp_ttl_seconds)


def _deliver(challenge_id: str, to: str, code: str) -> None:
    """Hand the code to the SMS provider, absorbing any failure.

    A send that failed only for numbers we hold would be a way to learn who has
    an account, so the caller gets the same response either way and the code is
    simply never delivered. The operator signal is the log line.

    The challenge is deliberately left pending rather than consumed or deleted.
    Consuming it would clear the resend cooldown, because the cooldown is
    measured from the newest unconsumed challenge, and a provider outage would
    then let anyone hammer the SMS gateway without limit. Deleting it would
    clear it too. Leaving it is inert: the code was never sent, so nobody can
    present it, and the next request supersedes it.
    """
    try:
        send_otp(to=to, code=code)
    except SmsDeliveryError:
        logger.error(
            "OTP delivery failed for challenge %s; code was not delivered.", challenge_id
        )


def _challenge_envelope(challenge_id: str, purpose: str, code: str | None) -> dict[str, Any]:
    """The shape every challenge response uses.

    `code` is only ever included outside production, so the demo can show it
    without a real SMS provider. It is filled in for unknown numbers too:
    a field that appears for some callers and not others is itself a tell.
    """
    settings = get_settings()
    payload: dict[str, Any] = {
        "challenge_id": challenge_id,
        "purpose": purpose,
        "expires_in_seconds": settings.otp_ttl_seconds,
        "resend_after_seconds": settings.otp_resend_cooldown_seconds,
    }
    if code is not None and not settings.is_production:
        payload["demo_code"] = code
    return payload


def _challenge_response(challenge: AuthChallenge, code: str, expires_in: int) -> dict[str, Any]:
    payload = _challenge_envelope(challenge.id, challenge.purpose, code)
    payload["expires_in_seconds"] = expires_in
    return payload


def signup(
    db: Session,
    *,
    role: str,
    phone: str,
    email: str | None,
    password: str | None,
    name: str,
    context: str | None = None,
    terms_accepted: bool = False,
    business_name: str | None = None,
    business_category: str | None = None,
    background_tasks: BackgroundTasks | None = None,
) -> dict[str, Any]:
    if role not in ASSIGNABLE_ROLES:
        # Bank and admin accounts are provisioned, never self-assigned at signup.
        raise HTTPException(status_code=400, detail="That account type cannot be self-registered.")

    if role == INDIVIDUAL_ROLE and not terms_accepted:
        raise HTTPException(status_code=400, detail="You must accept the terms to continue.")
    if role == VENDOR_ROLE and (not business_name or not business_category):
        raise HTTPException(status_code=400, detail="Vendor accounts need a business name and category.")

    normalized = normalize_phone(phone)
    if _get_by_phone(db, normalized) is not None:
        raise HTTPException(status_code=409, detail="An account already exists for that phone number.")
    if (email is None) != (password is None):
        raise HTTPException(status_code=400, detail="Provide both email address and password.")
    if email is None and get_settings().is_production:
        raise HTTPException(status_code=400, detail="Email address and password are required.")

    normalized_email = _normalise_email(email) if email is not None else None
    if normalized_email is not None:
        existing_email = db.execute(select(User).where(func.lower(User.email) == normalized_email)).scalars().first()
        if existing_email is not None:
            raise HTTPException(status_code=409, detail="An account already exists for that email address.")
    try:
        password_hash = hash_password(password) if password is not None else None
    except PasswordTooLong as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    now = datetime.utcnow()
    user = User(
        id=str(uuid.uuid4()),
        name=name.strip(),
        phone=normalized,
        email=normalized_email,
        password_hash=password_hash,
        role=role,
        context=context if role == INDIVIDUAL_ROLE else None,
        terms_accepted_at=now if terms_accepted else None,
    )
    db.add(user)

    if role == VENDOR_ROLE:
        # The guard above rejects a vendor signup without these, but that check sits
        # on a different condition, so nothing narrows them to str here.
        vendor_name = business_name or ""
        vendor_category = business_category or ""
        vendor = Vendor(
            id=str(uuid.uuid4()),
            name=vendor_name.strip(),
            category=vendor_category.strip(),
            verified_at=None,
        )
        db.add(vendor)
        db.flush()
        user.vendor_id = vendor.id
    db.commit()

    challenge, code = _issue_challenge(db, user, PURPOSE_SIGNUP, background_tasks=background_tasks)
    return _challenge_response(challenge, code, get_settings().otp_ttl_seconds)


def login(
    db: Session,
    identifier: str,
    password: str | None,
    device_token: str | None = None,
    background_tasks: BackgroundTasks | None = None,
) -> dict[str, Any]:
    """Password sign-in with five-day, device-bound OTP step-up.

    A password alone never suppresses OTP across every browser.  Only a random
    device credential issued after a verified OTP does so, and it expires after
    five days without sliding.  That fulfils the low-friction requirement
    without turning another person's recent login into an MFA bypass.
    """
    if password is None:
        # Kept only to avoid stranding locally seeded demo accounts while the
        # password-enrolment screen rolls out. It is never available in a
        # production deployment and the PWA no longer calls it.
        if get_settings().is_production:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_CREDENTIALS_ERROR)
        user = _get_by_identifier(db, identifier)
        if user is None:
            return _challenge_envelope(str(uuid.uuid4()), PURPOSE_LOGIN, generate_otp())
        challenge, code = _issue_challenge(db, user, PURPOSE_LOGIN, background_tasks=background_tasks)
        return _challenge_response(challenge, code, get_settings().otp_ttl_seconds)

    user = _get_by_identifier(db, identifier)
    password_hash = user.password_hash if user is not None and user.password_hash else _DECOY_PASSWORD_HASH
    if user is None or user.password_hash is None or not verify_password(password, password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_CREDENTIALS_ERROR)

    if _has_valid_trusted_device(db, user, device_token):
        return _token_response(user, trusted_device_token=None, otp_required=False)

    challenge, code = _issue_challenge(db, user, PURPOSE_LOGIN, background_tasks=background_tasks)
    payload = _challenge_response(challenge, code, get_settings().otp_ttl_seconds)
    payload["otp_required"] = True
    return payload


def verify_otp(db: Session, challenge_id: str, code: str) -> dict[str, Any]:
    settings = get_settings()
    challenge = db.get(AuthChallenge, challenge_id)
    if challenge is None:
        # login() hands back a well-formed challenge_id for numbers we do not
        # know, so a distinct 404 here would tell an attacker which numbers
        # exist. Answer exactly as we do for a wrong code.
        raise HTTPException(status_code=401, detail="Incorrect code.")

    if challenge.consumed_at is not None:
        raise HTTPException(status_code=400, detail="This code has already been used.")

    if challenge.expires_at is not None and datetime.utcnow() > challenge.expires_at:
        raise HTTPException(status_code=400, detail="This code has expired. Request a new one.")

    if challenge.attempts >= settings.otp_max_attempts:
        raise HTTPException(status_code=429, detail="Too many incorrect attempts. Request a new code.")

    if not otp_matches(code, challenge.salt, challenge.code_hash):
        challenge.attempts += 1
        db.commit()
        raise HTTPException(status_code=401, detail="Incorrect code.")

    user = db.get(User, challenge.user_id)
    if user is None:
        # The account went away between the code being issued and being used.
        # 404 here would confirm the challenge was genuine, which is the
        # enumeration signal login() is careful not to give away.
        raise HTTPException(status_code=401, detail="Incorrect code.")

    # Single use: consumed before the token is issued, so a replay of the same
    # code cannot mint a second session.
    challenge.consumed_at = datetime.utcnow()
    if challenge.purpose == PURPOSE_SIGNUP and user.phone_verified_at is None:
        user.phone_verified_at = challenge.consumed_at
    trusted_device_token = _issue_trusted_device(db, user) if challenge.purpose in {PURPOSE_SIGNUP, PURPOSE_LOGIN} else None
    db.commit()

    return _token_response(user, trusted_device_token=trusted_device_token, otp_required=False)


def _token_response(user: User, *, trusted_device_token: str | None, otp_required: bool) -> dict[str, Any]:
    response: dict[str, Any] = {
        "access_token": create_token(user.id, {"role": user.role}),
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role,
        "otp_required": otp_required,
    }
    if trusted_device_token is not None:
        response["trusted_device_token"] = trusted_device_token
        response["trusted_device_expires_in_seconds"] = TRUSTED_DEVICE_DAYS * 24 * 60 * 60
    return response


def issue_token_for(db: Session, user_id: str) -> dict[str, Any]:
    """Token for an already-provisioned user. Used by the demo role switcher."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Account not found.")
    return {
        "access_token": create_token(user.id, {"role": user.role}),
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role,
    }


def get_profile(db: Session, user_id: str) -> dict[str, Any]:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Account not found.")

    profile: dict[str, Any] = {
        "user_id": user.id,
        "name": user.name,
        "phone": user.phone,
        "role": user.role,
        "context": user.context,
        "institution_id": user.institution_id,
        "terms_accepted_at": user.terms_accepted_at,
        "phone_verified_at": user.phone_verified_at,
        "verified": user.verified_at is not None,
    }

    if user.role == VENDOR_ROLE and user.vendor_id:
        vendor = db.get(Vendor, user.vendor_id)
        profile["vendor"] = (
            {
                "vendor_id": vendor.id,
                "name": vendor.name,
                "category": vendor.category,
                "verified": vendor.verified_at is not None,
            }
            if vendor is not None
            else None
        )

    return profile


def revoke_session(
    db: Session,
    token_id: str | None,
    user_id: str | None,
    *,
    reason: str = "logout",
    expires_at: datetime | None = None,
) -> dict[str, Any]:
    """Mark one session as signed out.

    The row lives until the token it names would have expired anyway. Presenting
    that token afterwards is refused by signature validation, so keeping the row
    longer would only grow the table with entries that can never match.
    """
    if not token_id:
        # A token minted before this column existed carries no identifier, so it
        # cannot be revoked individually. It is refused at its own expiry.
        return {"status": "signed_out", "revoked": False}

    existing = db.get(SessionRevocation, token_id)
    if existing is not None:
        return {"status": "signed_out", "revoked": False}

    # Render has no background worker, so the only safe time to sweep the table
    # is on request. A purge here caps the revocation set at roughly one row per
    # logout per token lifetime, and the deleted rows can never match a live
    # token anyway.
    purge_expired_revocations(db)

    now = datetime.utcnow()
    db.add(
        SessionRevocation(
            jti=token_id,
            user_id=user_id or "",
            reason=reason,
            revoked_at=now,
            expires_at=expires_at or (now + timedelta(days=30)),
        )
    )
    db.commit()
    return {"status": "signed_out", "revoked": True}


def purge_expired_revocations(db: Session) -> int:
    """Drop revocations whose token has expired and can no longer be presented."""
    removed = db.query(SessionRevocation).filter(SessionRevocation.expires_at <= datetime.utcnow()).delete(synchronize_session=False)
    db.commit()
    return removed
