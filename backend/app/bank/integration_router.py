"""Machine API for bank systems, authenticated with scoped Sura API keys."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.bank import service
from app.bank.dependencies import BankApiPrincipal, require_api_scope
from app.database import get_db


router = APIRouter(prefix="/v1/integrations", tags=["bank integrations"])


@router.get("/customers/{user_id}/score")
def customer_score(
    user_id: str,
    current: BankApiPrincipal = Depends(require_api_scope("score:read")),
    db: Session = Depends(get_db),
):
    response = service.get_user_score(db, current.bank_id, f"api_key:{current.api_key_id}", user_id)
    db.commit()
    return response


@router.get("/customers/{user_id}/commitments")
def customer_commitments(
    user_id: str,
    current: BankApiPrincipal = Depends(require_api_scope("commitments:read")),
    db: Session = Depends(get_db),
):
    return service.get_user_commitments(db, current.bank_id, user_id)
