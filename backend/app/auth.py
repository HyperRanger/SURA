import json
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.bank.models import BankStaff
from app.database import get_db
from app.models import SessionRevocation, User
from core.config import get_settings
from core.security import is_local_session, token_issued_before, verify_token

bearer_scheme = HTTPBearer(auto_error=False)


def _finish_authorization_read(db: Session) -> None:
    """End the read-only transaction opened while resolving a local session.

    SQLAlchemy starts a transaction for ``db.get`` and ``query``. Domain write
    services then deliberately open their own atomic transaction, so leaving
    the authentication read open makes a valid first-party request fail with
    ``A transaction is already begun``. Authentication runs before route work,
    therefore rolling back this read-only unit cannot discard application data.
    """
    if db.in_transaction():
        db.rollback()


@dataclass
class AuthPrincipal:
    user_id: str
    role: str | None = None
    institution_id: str | None = None
    vendor_id: str | None = None
    is_local_session: bool = False
    permissions: frozenset[str] = frozenset()

    @property
    def can_verify_vendor(self) -> bool:
        return self.role in {"admin", "verifier"} or "vendor:verify" in self.permissions

    @property
    def can_redeem_vendor_vouchers(self) -> bool:
        return self.role == "vendor" or "vendor:redeem" in self.permissions


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AuthPrincipal:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    try:
        claims = verify_token(credentials.credentials)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token.") from exc

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token.")

    if is_local_session(claims):
        # The token is only a statement about who signed in, not about what they
        # may do now. The database decides, so a demoted or deleted account stops
        # working on the next request rather than when the token happens to
        # expire. Claim permissions are dropped for the same reason: nothing here
        # grants them, so accepting them would mean trusting the token on the one
        # question the re-check exists to answer.
        user = db.get(User, user_id)
        if user is None:
            _finish_authorization_read(db)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is no longer active.")

        # A suspension ends access immediately rather than at token expiry, and
        # says why. A restriction does not: the member keeps read access so they
        # can see why they cannot transact, and the check at the point of payment
        # stops the money instead.
        if user.account_status == "suspended":
            _finish_authorization_read(db)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=user.restriction_reason or "This account is suspended.",
            )

        # Signing out has to end the session, not just ask the client to forget
        # the token. The lookup is keyed on the token's own identifier, so
        # revoking one session leaves every other session untouched.
        token_id = claims.get("jti")
        if token_id and db.get(SessionRevocation, token_id) is not None:
            _finish_authorization_read(db)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has been signed out.")

        # "Sign out everywhere" raises this instant, so any token minted before
        # it stops working even though it was never individually revoked.
        # "Sign out everywhere" raises this instant, so any token minted before
        # it stops working even though it was never individually revoked.
        if user.session_invalidated_at is not None:
            stale = token_issued_before(claims, user.session_invalidated_at)
            if stale:
                _finish_authorization_read(db)
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has been signed out.")

        # A session that goes quiet too long stops being a session. The client
        # gets the same 401 as a signed-out token, so "idle" and "logged out"
        # look identical and the PWA can just send the user back to sign-in.
        # Activity slides the window rather than resetting a fixed deadline:
        # that is the difference between "log out after inactivity" and a hard
        # session cap. The stamp is throttled so an active member writes at most
        # once a minute instead of on every request.
        settings = get_settings()
        last_activity = user.last_active_at
        now = datetime.utcnow()
        if last_activity is not None and (now - last_activity) > timedelta(
            seconds=settings.session_idle_timeout_seconds
        ):
            _finish_authorization_read(db)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired. Sign in again.")

        if last_activity is None or (now - last_activity) >= timedelta(
            seconds=settings.last_activity_stamp_interval_seconds
        ):
            user.last_active_at = now
            db.commit()

        # A Bank Portal sign-in stores its role and permissions on the staff
        # record, not on the user row, so revoking or re-roling staff takes
        # effect on the next request instead of at token expiry.
        staff = db.query(BankStaff).filter(BankStaff.user_id == user.id).one_or_none()
        if staff is not None:
            if staff.status != "active":
                _finish_authorization_read(db)
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is no longer active.")
            staff_user_id = user.id
            staff_role = staff.role
            staff_bank_id = staff.bank_id
            staff_permissions = frozenset(json.loads(staff.permissions_json))
            _finish_authorization_read(db)
            return AuthPrincipal(
                user_id=staff_user_id,
                role=staff_role,
                # The bank tenant, which is the value the external provider puts in
                # the `institution_id` claim. It is not `users.institution_id`,
                # which is the school or employer on the customer record and has
                # nothing to do with bank scoping.
                institution_id=staff_bank_id,
                is_local_session=True,
                permissions=staff_permissions,
            )

        local_user_id = user.id
        local_role = user.role
        local_bank_id = user.bank_id
        local_vendor_id = user.vendor_id
        _finish_authorization_read(db)
        return AuthPrincipal(
            user_id=local_user_id,
            role=local_role,
            institution_id=local_bank_id,
            vendor_id=local_vendor_id,
            is_local_session=True,
            permissions=frozenset(),
        )

    # Externally issued token, trusted on its claims per the provider contract.
    return AuthPrincipal(
        user_id=user_id,
        role=claims.get("role"),
        institution_id=claims.get("institution_id"),
        vendor_id=claims.get("vendor_id"),
        permissions=frozenset(claims.get("permissions") or []),
    )
