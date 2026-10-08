"""Member funding-source routes.

These routes never initiate a transfer.  They support the transparent funding
label shown before the existing simulated contribution flow.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal, get_current_principal
from app.database import get_db
from app.schemas import AccountResolveRequest, LinkAccountRequest
from app.services import linked_accounts


router = APIRouter(prefix="/v1", tags=["linked accounts"])


def _require_individual(current_user: AuthPrincipal) -> None:
    if current_user.role != "individual":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member access is required.")


@router.get("/banks")
def list_nigerian_banks():
    return linked_accounts.list_banks()


@router.post("/accounts/resolve")
def resolve_account(payload: AccountResolveRequest, current_user: AuthPrincipal = Depends(get_current_principal)):
    _require_individual(current_user)
    return linked_accounts.resolve_account(payload.bank_name, payload.account_number)


@router.post("/accounts/link", status_code=status.HTTP_201_CREATED)
def link_account(
    payload: LinkAccountRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    return linked_accounts.link_account(db, current_user.user_id, payload.bank_name, payload.account_number)


@router.get("/me/account")
def get_my_linked_account(
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    account = linked_accounts.get_linked_account(db, current_user.user_id)
    return {"account": account}
