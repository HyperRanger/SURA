"""B1: Bank Portal sign-in.

Three decisions shape this file.

The password is checked with a constant-cost hash comparison, and every failure
returns the same message, so the endpoint cannot be used to find staff email
addresses.

A locked account is only reported as locked once the password is known to be
correct. Reporting it earlier would hand an attacker a way to discover which
staff accounts exist, which is exactly the thing the generic failure message is
there to prevent. The person who is actually locked still sees a clear state,
because they get past the password check.

Bank roles and permissions are read from ``bank_staff`` on every request rather
than trusted from the token, so revoking a staff member takes effect
immediately.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.bank.contracts import BANK_PORTAL_ROLES
from app.bank.models import BankAuditEvent, BankPartner, BankStaff
from app.models import AuthChallenge, User
from app.services import auth_service
from core.config import get_settings
from core.passwords import PasswordTooLong, hash_password, verify_password
from core.security import create_token, otp_matches

logger = logging.getLogger(__name__)


BANK_STAFF_STATUS_ACTIVE = "active"

GENERIC_CREDENTIALS_ERROR = "Email or password is incorrect."

# Compared against when no staff record matches, so an unknown address costs the
# same as a wrong password. Computed once at import: hashing per request would add
# a full bcrypt round to every miss for no extra protection.
_DECOY_HASH = hash_password("decoy-password-for-constant-work")


def _now() -> datetime:
    return datetime.utcnow()


def _audit(
    db: Session,
    bank_id: str,
    actor_id: str,
    event_type: str,
    subject_type: str,
    subject_id: str,
    details: dict | None = None,
) -> None:
    db.add(
        BankAuditEvent(
            id=str(uuid.uuid4()),
            bank_id=bank_id,
            actor_id=actor_id,
            event_type=event_type,
            subject_type=subject_type,
            subject_id=subject_id,
            detail_json=json.dumps(details or {}),
            occurred_at=_now(),
        )
    )


def _get_staff_by_email(db: Session, email: str) -> BankStaff | None:
    return (
        db.query(BankStaff)
        .filter(func.lower(BankStaff.email) == email.strip().lower())
        .one_or_none()
    )


def _is_locked(staff: BankStaff, now: datetime) -> bool:
    return staff.locked_until is not None and now < staff.locked_until


def _record_failed_password(db: Session, staff: BankStaff) -> None:
    settings = get_settings()
    staff.failed_password_attempts = (staff.failed_password_attempts or 0) + 1
    locked = False
    if staff.failed_password_attempts >= settings.bank_login_max_password_attempts:
        staff.locked_until = _now() + timedelta(seconds=settings.bank_login_lockout_seconds)
        staff.failed_password_attempts = 0
        locked = True
    _audit(
        db,
        staff.bank_id,
        staff.user_id,
        "account_locked" if locked else "bank_login_failed",
        "bank_staff",
        staff.id,
    )
    db.commit()


def _check_role(staff: BankStaff) -> None:
    """Refuse a staff row whose role the bank routes would not recognise.

    Without this the account signs in successfully and then fails every request
    with a 403 that reads as a permissions problem. Checked after the password is
    proven, so it does not tell an unauthenticated caller that a given address
    exists and is misconfigured.
    """
    if staff.role not in BANK_PORTAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not configured for Bank Portal access. Contact your administrator.",
        )


def _session_for(db: Session, staff: BankStaff) -> dict[str, Any]:
    # Re-checked here as well, because the role can change between the password
    # step and the second factor.
    _check_role(staff)

    staff.last_login_at = _now()
    staff.failed_password_attempts = 0
    _audit(db, staff.bank_id, staff.user_id, "bank_login_succeeded", "bank_staff", staff.id)
    db.commit()

    return {
        "access_token": create_token(
            staff.user_id,
            {"role": staff.role, "institution_id": staff.bank_id},
        ),
        "token_type": "bearer",
        "user_id": staff.user_id,
        "role": staff.role,
        "institution_id": staff.bank_id,
        "permissions": sorted(json.loads(staff.permissions_json)),
        "mfa": False,
    }


def _mfa_challenge(db: Session, staff: BankStaff, user: User) -> dict[str, Any]:
    challenge, code = auth_service.issue_otp_challenge(
        db, user, auth_service.PURPOSE_BANK_MFA, deliver_to=staff.mfa_phone
    )
    _audit(db, staff.bank_id, staff.user_id, "bank_mfa_challenged", "bank_staff", staff.id)
    db.commit()

    settings = get_settings()
    payload: dict[str, Any] = {
        "challenge_id": challenge.id,
        "purpose": auth_service.PURPOSE_BANK_MFA,
        "mfa_required": True,
        "expires_in_seconds": settings.otp_ttl_seconds,
        "resend_after_seconds": settings.otp_resend_cooldown_seconds,
    }
    if not settings.is_production:
        payload["demo_code"] = code
    return payload


def login(db: Session, email: str, password: str) -> dict[str, Any]:
    """Email and password, then a second factor when the account has one."""
    settings = get_settings()
    staff = _get_staff_by_email(db, email)

    if staff is None or staff.status != BANK_STAFF_STATUS_ACTIVE:
        # Burn the same work either way, so a missing address and a wrong
        # password are not separable by response time.
        verify_password(password, _DECOY_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_CREDENTIALS_ERROR
        )

    try:
        password_ok = verify_password(password, staff.password_hash)
    except (PasswordTooLong, ValueError):
        password_ok = False

    if not password_ok:
        _record_failed_password(db, staff)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_CREDENTIALS_ERROR
        )

    # Past this point the caller has proved they hold the password, so it is safe
    # to tell them the account is locked.
    if _is_locked(staff, _now()):
        _audit(db, staff.bank_id, staff.user_id, "bank_login_blocked_locked", "bank_staff", staff.id)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="This account is temporarily locked. Try again later or contact your administrator.",
        )

    user = db.get(User, staff.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_CREDENTIALS_ERROR
        )

    # Before the challenge, so a misconfigured account does not cost an SMS.
    _check_role(staff)

    if settings.bank_mfa_required:
        if not staff.mfa_phone:
            # Refuse rather than quietly issuing a session without the factor:
            # an account provisioned without a phone is a configuration mistake.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has no second factor configured. Contact your administrator.",
            )
        return _mfa_challenge(db, staff, user)

    return _session_for(db, staff)


def verify_mfa(db: Session, challenge_id: str, code: str) -> dict[str, Any]:
    """Consume the second factor and issue the Bank Portal session."""
    settings = get_settings()
    challenge = db.get(AuthChallenge, challenge_id)

    if challenge is None or challenge.purpose != auth_service.PURPOSE_BANK_MFA:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect code.")

    if challenge.consumed_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This code has already been used.")

    if challenge.expires_at is not None and _now() > challenge.expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This code has expired. Sign in again.")

    if challenge.attempts >= settings.otp_max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect attempts. Sign in again.",
        )

    if not otp_matches(code, challenge.salt, challenge.code_hash):
        challenge.attempts += 1
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect code.")

    staff = db.query(BankStaff).filter(BankStaff.user_id == challenge.user_id).one_or_none()
    if staff is None or staff.status != BANK_STAFF_STATUS_ACTIVE:
        # Answer as we do for a wrong code. A distinct response here would confirm
        # the code was genuine, which is the enumeration signal login() avoids.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect code.")

    # Consumed before the token is issued, so a replay cannot mint a second session.
    challenge.consumed_at = _now()
    db.commit()
    return _session_for(db, staff)


DEMO_BANK_STAFF_EMAIL = "demo.bank@sura.local"


def demo_login(db: Session) -> dict[str, Any]:
    """One-tap Bank Portal sign-in for the live demo.

    Disabled in production by the caller. It provisions a fully working staff
    record so the demo exercises the real session path rather than a shortcut
    around it.
    """
    now = _now()
    bank = db.query(BankPartner).filter(BankPartner.name == "Demo Bank").one_or_none()
    if bank is None:
        bank = BankPartner(id="bnk_demo", name="Demo Bank", created_at=now)
        db.add(bank)
        db.flush()

    user = db.get(User, "usr_demo_bank")
    if user is None:
        user = User(
            id="usr_demo_bank",
            name="Demo Bank Analyst",
            phone="demo-bank@sura.local",
            role="bank_risk_analyst",
            phone_verified_at=now,
            verified_at=now,
            bank_id=bank.id,
        )
        db.add(user)
        db.flush()
    elif user.bank_id != bank.id:
        user.bank_id = bank.id

    staff = _get_staff_by_email(db, DEMO_BANK_STAFF_EMAIL)
    if staff is None:
        staff = BankStaff(
            id="stf_demo_bank",
            bank_id=bank.id,
            user_id=user.id,
            email=DEMO_BANK_STAFF_EMAIL,
            password_hash=hash_password("demo-password-never-in-production"),
            role="bank_risk_analyst",
            permissions_json=json.dumps(
                [
                    "bank:overview:read",
                    "bank:users:read",
                    "bank:flags:read",
                    "bank:flags:write",
                    "bank:audit:read",
                ]
            ),
            mfa_phone="2347065250817",
            status=BANK_STAFF_STATUS_ACTIVE,
            created_at=now,
        )
        db.add(staff)
        db.commit()
    return _session_for(db, staff)
