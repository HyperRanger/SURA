import secrets
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal, bearer_scheme, get_current_principal
from app.database import get_db
from app.models import User, Vendor
from app.schemas import (
    DemoLoginAsRequest,
    DemoTokenRequest,
    LoginRequest,
    PasswordRecoveryConfirmRequest,
    PasswordRecoveryRequest,
    ResendOtpRequest,
    SignupRequest,
    VerifyOtpRequest,
)
from app.services import audit, auth_service
from core.config import get_settings
from core.security import create_token, is_local_session, token_expiry, verify_token

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
def signup(payload: SignupRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Creates a password account, then proves the supplied phone by OTP."""
    return auth_service.signup(
        db,
        role=payload.role,
        phone=payload.phone,
        email=payload.email,
        password=payload.password,
        name=payload.business_name if payload.role == "vendor" and payload.business_name else payload.name,
        context=payload.context,
        terms_accepted=payload.terms_accepted,
        business_name=payload.business_name,
        business_category=payload.business_category,
        background_tasks=background_tasks,
    )


@router.post("/login")
def login(payload: LoginRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Signs in by password; a new or expired device receives OTP step-up."""
    return auth_service.login(
        db,
        payload.identifier or payload.phone or "",
        payload.password,
        payload.device_token,
        background_tasks,
    )


@router.post("/verify-otp")
def verify_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    """P4. Consumes the code and returns the session token carrying the role."""
    return auth_service.verify_otp(db, payload.challenge_id, payload.code)


@router.post("/resend-otp")
def resend_otp(payload: ResendOtpRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return auth_service.resend_otp(db, payload.challenge_id, background_tasks)


@router.post("/password-recovery")
def password_recovery(payload: PasswordRecoveryRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Kick off self-service recovery with an SMS code to the member's phone.

    Answers identically for an unknown identifier, so it never confirms who has
    an account. The code is delivered by SMS because recovery must reach the
    person who holds the phone, and that is the contact Sura can actually send to.
    """
    return auth_service.request_password_recovery(db, payload.identifier, background_tasks)


@router.post("/password-recovery/confirm")
def password_recovery_confirm(payload: PasswordRecoveryConfirmRequest, db: Session = Depends(get_db)):
    """Verify the recovery code and set the new password.

    Ends every session and every remembered device, so a stolen token minted
    before the reset stops working immediately.
    """
    return auth_service.confirm_password_recovery(db, payload.challenge_id, payload.code, payload.new_password)


@profile_router.get("/me")
def me(
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """The signed-in account, including the role the backend assigned."""
    return auth_service.get_profile(db, current_user.user_id)


@profile_router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """End this session immediately.

    Records the token's identifier so the same token is refused on the next
    request. Idempotent, and succeeds on a token that has already expired or
    already been revoked, because the caller's intent is to be signed out and
    that is true either way.
    """
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    try:
        claims = verify_token(credentials.credentials)
    except Exception:
        # An expired or malformed token is already useless, so there is nothing
        # to revoke. Reporting success rather than an error keeps the endpoint
        # safe to call twice from a client that just lost connectivity.
        return {"status": "signed_out"}

    if not is_local_session(claims):
        # Externally issued tokens are revoked at the provider, so recording one
        # locally would claim a revocation that never happened.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This session is issued by an external identity provider and must be ended there.",
        )

    result = auth_service.revoke_session(
        db,
        claims.get("jti"),
        claims.get("sub"),
        expires_at=token_expiry(claims),
    )
    audit.record(
        db,
        event_type=audit.LOGOUT,
        subject_type="user",
        subject_id=str(claims.get("sub") or ""),
        actor_id=str(claims.get("sub") or ""),
        actor_role=claims.get("role"),
        detail={"revoked": result["revoked"]},
    )
    db.commit()
    return result


@profile_router.post("/logout-all")
def logout_all(
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """End every session this person holds.

    Raises an instant on the account that any token issued before it fails the
    re-check, so a device that never called logout is covered too.
    """
    user = db.get(User, current_user.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    user.session_invalidated_at = datetime.utcnow()
    trusted_devices_ended = auth_service.revoke_trusted_devices(db, user.id)
    audit.record(
        db,
        event_type=audit.LOGOUT_ALL,
        subject_type="user",
        subject_id=user.id,
        actor_id=user.id,
        actor_role=user.role,
        detail={"sessions_ended": "all", "trusted_devices_ended": trusted_devices_ended},
    )
    db.commit()
    return {
        "status": "signed_out",
        "sessions_ended": "all",
        "trusted_devices_ended": trusted_devices_ended,
    }


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
