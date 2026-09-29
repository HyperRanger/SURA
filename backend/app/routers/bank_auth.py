"""B1: Bank Portal sign-in routes.

Separate from ``app/bank/router.py`` because these are the endpoints a bank
analyst uses before they have a session, and everything in that router requires
one. Adding them there would mean a router that both issues and consumes
sessions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import BankLoginRequest, BankVerifyMfaRequest
from app.services import bank_auth_service
from core.config import get_settings


router = APIRouter(prefix="/v1/bank", tags=["bank portal auth"])


def _require_not_production() -> None:
    if get_settings().is_production:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")


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


@router.post("/demo-login")
def bank_demo_login(db: Session = Depends(get_db)):
    """One-tap Bank Portal sign-in for the live demo.

    404 in production, like every other demo affordance: it hands out a working
    bank session with no credential check.
    """
    _require_not_production()
    return bank_auth_service.demo_login(db)
