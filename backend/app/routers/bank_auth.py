"""B1: Bank Portal sign-in routes.

Separate from ``app/bank/router.py`` because these are the endpoints a bank
analyst uses before they have a session, and everything in that router requires
one. Adding them there would mean a router that both issues and consumes
sessions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal, bearer_scheme, get_current_principal
from app.bank.models import BankStaff
from app.database import get_db
from app.schemas import BankChangePasswordRequest, BankLoginRequest, BankVerifyMfaRequest
from app.services import bank_auth_service
from core.config import get_settings
from core.security import verify_token

router = APIRouter(prefix="/v1/bank", tags=["bank portal auth"])


def _require_not_production() -> None:
    if get_settings().is_production:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")


def _staff_for_current_principal(db: Session, current: AuthPrincipal) -> BankStaff:
    """The staff row behind a Bank Portal session.

    An external identity-provider session has no ``bank_staff`` row to change a
    password against. Say so plainly rather than silently succeeding.
    """
    staff = db.query(BankStaff).filter(BankStaff.user_id == current.user_id).one_or_none()
    if staff is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This session is issued by an external identity provider and manages no local password.",
        )
    return staff


@router.post("/login")
def bank_login(payload: BankLoginRequest, db: Session = Depends(get_db)):
    """Email and password. Returns an MFA challenge when a second factor is on.

    Answers with 401 for an unknown address and for a wrong password alike, so
    it cannot be used to enumerate staff.
    """
    return bank_auth_service.login(db, payload.email, payload.password)


@router.post("/login/verify")
def bank_login_verify(payload: BankVerifyMfaRequest, db: Session = Depends(get_db)):
    """Consume the second factor and return the Bank Portal session."""
    return bank_auth_service.verify_mfa(db, payload.challenge_id, payload.code)


@router.post("/logout")
def bank_logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """End this Bank Portal session immediately.

    Records the token identifier so the same token is refused on its next
    request, rather than relying on the client to forget it. Idempotent.
    """
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    try:
        claims = verify_token(credentials.credentials)
    except Exception:
        # Already unusable, so there is nothing to revoke. Reporting success
        # keeps the endpoint safe to call twice from a client that just
        # reconnected.
        return {"status": "signed_out"}

    result = bank_auth_service.revoke_bank_session(db, claims)
    bank_auth_service.audit.record(
        db,
        event_type=bank_auth_service.audit.LOGOUT,
        subject_type="bank_staff",
        subject_id=str(claims.get("sub") or ""),
        actor_id=str(claims.get("sub") or ""),
        actor_role=claims.get("role"),
        institution_id=claims.get("institution_id"),
        detail={"revoked": result["revoked"]},
    )
    db.commit()
    return result


@router.post("/password")
def bank_change_password(
    payload: BankChangePasswordRequest,
    current: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Change your own password.

    Requires the current password, so a session that was stolen cannot quietly
    become permanent access. Every session you hold ends, including this one.
    """
    staff = _staff_for_current_principal(db, current)
    return bank_auth_service.change_password(db, staff, payload.current_password, payload.new_password)


@router.post("/demo-login")
def bank_demo_login(db: Session = Depends(get_db)):
    """One-tap Bank Portal sign-in for the live demo.

    404 in production, like every other demo affordance: it hands out a working
    bank session with no credential check.
    """
    _require_not_production()
    return bank_auth_service.demo_login(db)
