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

from app.bank.contracts import BANK_PORTAL_ROLES, BANK_STAFF_ROLE_PERMISSIONS
from app.bank.models import BankAuditEvent, BankPartner, BankStaff
from app.models import AuthChallenge, User
from app.services import audit, auth_service
from app.services.demo_data import DEMO_BANK_ID, DEMO_BANK_PASSWORD, DEMO_PARTNER_BANK
from core.config import get_settings
from core.passwords import PasswordTooLong, hash_password, verify_password
from core.security import create_token, is_local_session, otp_matches, token_expiry

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


def _audit_platform(
    db: Session,
    event_type: str,
    subject_type: str,
    subject_id: str,
    *,
    actor_id: str | None = None,
    actor_role: str | None = None,
    bank_id: str | None = None,
    detail: dict | None = None,
) -> None:
    """The same event, at platform scope.

    Mirrored rather than merged: the bank trail stays answerable without a
    platform-wide read, and the platform trail survives a bank's own retention
    window.
    """
    audit.record(
        db,
        event_type=event_type,
        subject_type=subject_type,
        subject_id=subject_id,
        actor_id=actor_id,
        actor_role=actor_role,
        institution_id=bank_id,
        detail=detail,
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
    _audit_platform(
        db,
        audit.ACCOUNT_LOCKED if locked else audit.LOGIN_FAILED,
        "bank_staff",
        staff.id,
        actor_id=None,
        actor_role="bank_staff",
        bank_id=staff.bank_id,
        # No email recorded: the subject is the staff id, which is resolvable by
        # anyone authorised to read the trail and useless to anyone who is not.
        detail={"outcome": "locked" if locked else "rejected"},
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
    _audit_platform(
        db,
        audit.LOGIN_SUCCEEDED,
        "bank_staff",
        staff.id,
        actor_id=staff.user_id,
        actor_role=staff.role,
        bank_id=staff.bank_id,
    )
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
    # Recorded here rather than only at session issue, because a person who
    # clears the password and then abandons the second factor still got the
    # password right, and "who tried" is the question this trail exists for.
    _audit_platform(
        db,
        audit.LOGIN_MFA_CHALLENGED,
        "bank_staff",
        staff.id,
        actor_id=staff.user_id,
        actor_role=staff.role,
        bank_id=staff.bank_id,
        detail={"outcome": "mfa_pending"},
    )
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


MIN_PASSWORD_LENGTH = 12


def _validate_new_password(staff: BankStaff, new_password: str) -> None:
    """Refuse a password we would not have accepted at signup.

    Length and a check against the account's own identifiers are enforced before
    hashing, so a rejected password costs nothing and the reason can be specific.
    """
    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters.",
        )

    try:
        hash_password(new_password)
    except PasswordTooLong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is too long.",
        ) from None

    lowered = new_password.lower()
    identifiers = [part for part in (staff.email.split("@")[0], staff.email, staff.user_id) if part]
    if any(part.lower() in lowered for part in identifiers):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must not contain your email or user ID.",
        )


def change_password(db: Session, staff: BankStaff, current_password: str, new_password: str) -> dict[str, Any]:
    """Change your own password. Requires the current one.

    Re-proving possession is the point. A stolen session that reaches this
    endpoint still cannot take the account over permanently without the old
    password.
    """
    try:
        current_ok = verify_password(current_password, staff.password_hash)
    except (PasswordTooLong, ValueError):
        current_ok = False

    if not current_ok:
        _record_failed_password(db, staff)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_CREDENTIALS_ERROR
        )

    if verify_password(new_password, staff.password_hash):
        # Otherwise the account could be walked down to a password it already had.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current one.",
        )

    _validate_new_password(staff, new_password)

    now = _now()
    staff.password_hash = hash_password(new_password)
    staff.password_changed_at = now
    staff.failed_password_attempts = 0
    staff.locked_until = None

    # Every session this person holds was proved by the old password, so all of
    # them are no longer trustworthy. The user row is the invalidation point,
    # because live tokens are deliberately not stored.
    user = db.get(User, staff.user_id)
    if user is not None:
        user.session_invalidated_at = now

    _audit(db, staff.bank_id, staff.user_id, "bank_password_changed", "bank_staff", staff.id)
    _audit_platform(
        db,
        audit.PASSWORD_CHANGED,
        "bank_staff",
        staff.id,
        actor_id=staff.user_id,
        actor_role=staff.role,
        bank_id=staff.bank_id,
    )
    db.commit()
    return {"status": "password_changed", "sessions_revoked": True, "changed_at": now.isoformat()}


def reset_password(db: Session, actor: BankStaff, target_staff_id: str, new_password: str) -> dict[str, Any]:
    """Set a colleague's password. Administrators only.

    The recovery path for someone locked out of their own account. Refused for
    the actor's own account, because that would let a caller bypass proving
    possession of the current password.
    """
    if actor.role != "bank_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a bank administrator can reset another person's password.",
        )

    target = db.get(BankStaff, target_staff_id)
    if target is None or target.bank_id != actor.bank_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found.")

    if target.id == actor.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use the password change endpoint to change your own password.",
        )

    _validate_new_password(target, new_password)

    now = _now()
    target.password_hash = hash_password(new_password)
    target.password_changed_at = now
    target.failed_password_attempts = 0
    target.locked_until = None

    user = db.get(User, target.user_id)
    if user is not None:
        user.session_invalidated_at = now

    _audit(
        db,
        actor.bank_id,
        actor.user_id,
        "bank_password_reset",
        "bank_staff",
        target.id,
        {"role": target.role, "email_domain": target.email.split("@")[-1]},
    )
    _audit_platform(
        db,
        audit.PASSWORD_RESET,
        "bank_staff",
        target.id,
        actor_id=actor.user_id,
        actor_role=actor.role,
        bank_id=actor.bank_id,
        # The target's own identifiers are deliberately absent: who was reset is
        # the question an investigator asks, not something every audit reader
        # needs to see.
        detail={"role": target.role},
    )
    db.commit()
    return {"status": "password_reset", "staff_id": target.id, "sessions_revoked": True}


def revoke_bank_session(db: Session, claims: dict[str, Any]) -> dict[str, Any]:
    """Sign out one Bank Portal session.

    Bank staff sessions are minted here, so the same identifier-based revocation
    as member sessions applies. A session from the bank's own identity provider
    is refused, because recording it locally would claim a revocation that only
    the provider can perform.
    """
    if not is_local_session(claims):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This session is issued by an external identity provider and must be ended there.",
        )

    return auth_service.revoke_session(
        db,
        claims.get("jti"),
        claims.get("sub"),
        reason="bank_logout",
        expires_at=token_expiry(claims),
    )


def change_permissions(db: Session, actor: BankStaff, target_staff_id: str, permissions: list[str]) -> dict[str, Any]:
    """Replace a colleague's permission set. Administrators only.

    Raising someone's permissions and narrowing them are the same operation here,
    so the same permission guards both: an administrator is not a bypass for the
    role map in ``contracts``.
    """
    if actor.role != "bank_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a bank administrator can change permissions.",
        )

    target = db.get(BankStaff, target_staff_id)
    if target is None or target.bank_id != actor.bank_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found.")

    if target.id == actor.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own permissions.",
        )

    allowed = BANK_STAFF_ROLE_PERMISSIONS[target.role]
    rejected = sorted(set(permissions) - set(allowed))
    if rejected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role {target.role} does not carry: {', '.join(rejected)}",
        )

    target.permissions_json = json.dumps(sorted(permissions))
    _audit(
        db,
        actor.bank_id,
        actor.user_id,
        "bank_staff_permissions_changed",
        "bank_staff",
        target.id,
        {"permissions": sorted(permissions)},
    )
    _audit_platform(
        db,
        audit.STAFF_PERMISSIONS_CHANGED,
        "bank_staff",
        target.id,
        actor_id=actor.user_id,
        actor_role=actor.role,
        bank_id=actor.bank_id,
        detail={"permissions": sorted(permissions)},
    )
    db.commit()
    return {"staff_id": target.id, "permissions": sorted(permissions)}


DEMO_BANK_STAFF_EMAIL = "demo.admin@sura.local"
DEMO_BANK_STAFF_ROLE = "bank_admin"
DEMO_BANK_NAME = DEMO_PARTNER_BANK[1]
DEMO_BANK_STAFF_USER_ID = "usr_demo_bank_admin"


def demo_login(db: Session) -> dict[str, Any]:
    """One-tap Bank Portal sign-in for the live demo.

    Disabled in production by the caller. It provisions a fully working staff
    record so the demo exercises the real session path rather than a shortcut
    around it.
    """
    now = _now()
    bank = db.get(BankPartner, DEMO_BANK_ID)
    if bank is None:
        bank = BankPartner(id=DEMO_BANK_ID, name=DEMO_BANK_NAME, created_at=now)
        db.add(bank)
        db.flush()

    user = db.get(User, DEMO_BANK_STAFF_USER_ID)
    if user is None:
        user = User(
            id=DEMO_BANK_STAFF_USER_ID,
            name="Sura Partner Bank Portal Admin",
            phone=DEMO_BANK_STAFF_EMAIL,
            role=DEMO_BANK_STAFF_ROLE,
            phone_verified_at=now,
            verified_at=now,
            bank_id=bank.id,
        )
        db.add(user)
        db.flush()
    elif user.bank_id != bank.id:
        user.bank_id = bank.id
    user.role = DEMO_BANK_STAFF_ROLE

    staff = _get_staff_by_email(db, DEMO_BANK_STAFF_EMAIL)
    if staff is None:
        staff = BankStaff(
            id="stf_demo_bank_admin",
            bank_id=bank.id,
            user_id=user.id,
            email=DEMO_BANK_STAFF_EMAIL,
            password_hash=hash_password(DEMO_BANK_PASSWORD),
            role=DEMO_BANK_STAFF_ROLE,
            permissions_json=json.dumps(sorted(BANK_STAFF_ROLE_PERMISSIONS[DEMO_BANK_STAFF_ROLE])),
            mfa_phone="2347065250817",
            status=BANK_STAFF_STATUS_ACTIVE,
            created_at=now,
        )
        db.add(staff)
    else:
        # This endpoint is a non-production demo shortcut, so it must keep its
        # single demo identity fully usable after a prior run or a role change.
        staff.role = DEMO_BANK_STAFF_ROLE
        staff.permissions_json = json.dumps(sorted(BANK_STAFF_ROLE_PERMISSIONS[DEMO_BANK_STAFF_ROLE]))
        staff.status = BANK_STAFF_STATUS_ACTIVE
    db.commit()
    return _session_for(db, staff)
