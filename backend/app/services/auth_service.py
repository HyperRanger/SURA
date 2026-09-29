"""Signup, login and one-time-code verification.

The role is decided here and only here. Signup cannot be talked into a different
role by the request body, the code is issued by the server rather than supplied by
the client, and the issued token carries the role so protected endpoints can
re-check it. A challenge is single-use, time-limited and attempt-capped.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuthChallenge, User, Vendor
from core.config import get_settings
from core.security import create_token, generate_otp, hash_otp, new_otp_salt, otp_matches

INDIVIDUAL_ROLE = "individual"
VENDOR_ROLE = "vendor"
BANK_ROLE = "bank"
ADMIN_ROLE = "admin"

ASSIGNABLE_ROLES = {INDIVIDUAL_ROLE, VENDOR_ROLE}

PURPOSE_SIGNUP = "signup"
PURPOSE_LOGIN = "login"


NIGERIA_COUNTRY_CODE = "234"


def _normalize_phone(phone: str) -> str:
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


def _issue_challenge(db: Session, user: User, purpose: str) -> tuple[AuthChallenge, str]:
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
    return challenge, code


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
    name: str,
    context: str | None = None,
    terms_accepted: bool = False,
    business_name: str | None = None,
    business_category: str | None = None,
) -> dict[str, Any]:
    if role not in ASSIGNABLE_ROLES:
        # Bank and admin accounts are provisioned, never self-assigned at signup.
        raise HTTPException(status_code=400, detail="That account type cannot be self-registered.")

    if role == INDIVIDUAL_ROLE:
        if not terms_accepted:
            raise HTTPException(status_code=400, detail="You must accept the terms to continue.")
    if role == VENDOR_ROLE and (not business_name or not business_category):
        raise HTTPException(status_code=400, detail="Vendor accounts need a business name and category.")

    normalized = _normalize_phone(phone)
    if _get_by_phone(db, normalized) is not None:
        raise HTTPException(status_code=409, detail="An account already exists for that phone number.")

    now = datetime.utcnow()
    user = User(
        id=str(uuid.uuid4()),
        name=name.strip(),
        phone=normalized,
        role=role,
        context=context if role == INDIVIDUAL_ROLE else None,
        terms_accepted_at=now if terms_accepted else None,
    )
    db.add(user)

    if role == VENDOR_ROLE:
        vendor = Vendor(
            id=str(uuid.uuid4()),
            name=business_name.strip(),
            category=business_category.strip(),
            verified_at=None,
        )
        db.add(vendor)
        db.flush()
        user.vendor_id = vendor.id
    db.commit()

    challenge, code = _issue_challenge(db, user, PURPOSE_SIGNUP)
    return _challenge_response(challenge, code, get_settings().otp_ttl_seconds)


def login(db: Session, phone: str) -> dict[str, Any]:
    """Always answers in the same shape, so this cannot be used to discover
    who has an account.

    An unknown number gets a syntactically valid but unverifiable challenge
    rather than a 404. A distinguishable response is itself the leak, so the
    caller cannot tell the two cases apart from the body, the status, or the
    field set.
    """
    user = _get_by_phone(db, _normalize_phone(phone))

    if user is None:
        return _challenge_envelope(str(uuid.uuid4()), PURPOSE_LOGIN, generate_otp())

    challenge, code = _issue_challenge(db, user, PURPOSE_LOGIN)
    return _challenge_response(challenge, code, get_settings().otp_ttl_seconds)


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
    db.commit()

    return {
        "access_token": create_token(user.id, {"role": user.role}),
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role,
    }


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
