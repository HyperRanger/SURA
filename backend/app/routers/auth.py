import secrets

from fastapi import APIRouter, HTTPException, status

from app.schemas import DemoTokenRequest
from core.config import get_settings
from core.security import create_token

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/demo-token")
def create_demo_token(payload: DemoTokenRequest):
    """Demo-only token issuer; replace with the bank's identity provider in production."""
    settings = get_settings()
    if not secrets.compare_digest(payload.otp_code, settings.demo_otp_code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid demo OTP.")
    return {"access_token": create_token(payload.user_id), "token_type": "bearer"}
