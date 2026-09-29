import secrets
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal, get_current_principal
from app.database import get_db
from app.models import User, Vendor
from app.schemas import (
    DemoLoginAsRequest,
    DemoTokenRequest,
    LoginRequest,
    SignupRequest,
    VerifyOtpRequest,
)
from app.services import auth_service
from core.config import get_settings
from core.security import create_token

router = APIRouter(prefix="/v1/auth", tags=["auth"])
profile_router = APIRouter(prefix="/v1", tags=["auth"])
demo_router = APIRouter(prefix="/v1/demo", tags=["demo"])


def _require_not_production() -> None:
    if get_settings().is_production:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found.",
        )


@router.post("/demo-token")
def create_demo_token(payload: DemoTokenRequest):
    """Demo-only token issuer; replace with the bank's identity provider in production.

    Gated like every other demo affordance. It hands out a session for an
    arbitrary user_id with no credential check beyond a shared code, so leaving
    it open in production would let anyone impersonate any seeded account.
    """
    _require_not_production()

    settings = get_settings()
    if not secrets.compare_digest(payload.otp_code, settings.demo_otp_code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid demo OTP.")
    return {"access_token": create_token(payload.user_id), "token_type": "bearer"}


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """P2. Creates the account unverified and issues a code to prove the phone."""
    return auth_service.signup(
        db,
        role=payload.role,
        phone=payload.phone,
        name=payload.business_name if payload.role == "vendor" and payload.business_name else payload.name,
        context=payload.context,
        terms_accepted=payload.terms_accepted,
        business_name=payload.business_name,
        business_category=payload.business_category,
    )


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """P3. Always answers the same way for unknown numbers, so this cannot be
    used to discover who has an account."""
    return auth_service.login(db, payload.phone)


@router.post("/verify-otp")
def verify_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    """P4. Consumes the code and returns the session token carrying the role."""
    return auth_service.verify_otp(db, payload.challenge_id, payload.code)


@profile_router.get("/me")
def me(
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """The signed-in account, including the role the backend assigned."""
    return auth_service.get_profile(db, current_user.user_id)


DEMO_USER_IDS = {
    "individual": "usr_demo_individual",
    "vendor": "usr_demo_vendor",
    "bank": "usr_demo_bank",
}


@demo_router.post("/login-as")
def demo_login_as(payload: DemoLoginAsRequest, db: Session = Depends(get_db)):
    """P8. One-tap role switch for the live demo.

    Unavailable in production: this hands out a valid session for a seeded
    account with no credential check at all.
    """
    _require_not_production()

    user_id = DEMO_USER_IDS[payload.role]
    user = db.get(User, user_id)
    if user is None:
        user = User(
            id=user_id,
            name=f"Demo {payload.role.title()}",
            phone=f"demo-{payload.role}@sura.local",
            role=payload.role,
            phone_verified_at=datetime.utcnow(),
            verified_at=datetime.utcnow(),
        )
        if payload.role == "vendor":
            vendor = Vendor(
                id=str(uuid.uuid4()),
                name=user.name,
                category="demo",
                verified_at=None,
            )
            db.add(vendor)
            db.flush()
            user.vendor_id = vendor.id
        db.add(user)
        db.commit()

    return {
        "access_token": create_token(user.id, {"role": user.role}),
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role,
    }
