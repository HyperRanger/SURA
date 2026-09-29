from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import status
from sqlalchemy import text

from app.database import get_db
from app.routers.auth import router as auth_router
from sqlalchemy.orm import Session
from app.routers.commitments import consent_router, router as commitments_router
from app.routers.score import router as score_router
from app.routers.vendors import router as vendors_router
from app.bank.router import router as bank_router
from app.bank.integration_router import router as bank_integration_router

app = FastAPI(title="Sura API", version="1.0.0")

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
