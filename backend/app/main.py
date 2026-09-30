from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import status
from sqlalchemy import text

from app.database import get_db
from app.routers.auth import router as auth_router
from app.routers.auth import demo_router as demo_router
from app.routers.auth import profile_router as profile_router
from sqlalchemy.orm import Session
from app.routers.commitments import consent_router, router as commitments_router
from app.routers.score import router as score_router
from app.routers.vendors import router as vendors_router
from app.bank.router import router as bank_router
from app.bank.integration_router import router as bank_integration_router
from app.routers.bank_auth import router as bank_auth_router
from app.member_vendor.router import router as member_vendor_router
from core.config import get_settings


def _validate_production_settings() -> None:
    """Refuse to serve production without a way to deliver one-time codes.

    With no SMS provider, signup still returns a challenge but no code ever
    arrives, so every new account is unverifiable. That is a support queue that
    looks like a working signup, which is worse than not starting.
    """
    settings = get_settings()
    if settings.is_production and not settings.is_sms_configured:
        raise RuntimeError(
            "TERMII_API_KEY must be set in production: without it no one-time code "
            "can be delivered and no account can be verified."
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    _validate_production_settings()
    yield


app = FastAPI(title="Sura API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(commitments_router)
app.include_router(consent_router)
app.include_router(auth_router)
app.include_router(vendors_router)
app.include_router(score_router)
app.include_router(bank_router)
app.include_router(bank_integration_router)
app.include_router(bank_auth_router)
app.include_router(profile_router)
app.include_router(demo_router)
app.include_router(member_vendor_router)


def _check_database(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    database_ok = _check_database(db)
    response = {
        "status": "ok",
        "database": "ok" if database_ok else "unavailable",
    }
    if database_ok:
        return response
    response["status"] = "unavailable"
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=response)
