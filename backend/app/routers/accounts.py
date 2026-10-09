"""Member funding-source routes.

These routes never initiate a transfer.  They support the transparent funding
label shown before the existing simulated contribution flow.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal, get_current_principal
from app.database import get_db
from app.models import User
from app.schemas import AccountResolveRequest, LinkAccountRequest
from app.services import linked_accounts


router = APIRouter(prefix="/v1", tags=["linked accounts"])


def _require_individual(current_user: AuthPrincipal) -> None:
    if current_user.role != "individual":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member access is required.")


@router.get("/banks")
def list_nigerian_banks(db: Session = Depends(get_db)):
    return linked_accounts.list_banks(db)


@router.post("/accounts/resolve")
def resolve_account(
    payload: AccountResolveRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    user = db.get(User, current_user.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member account not found.")
    return linked_accounts.resolve_account(
        db,
        payload.bank_name,
        payload.account_number,
        payload.partner_bank_id,
        expected_subject_id=current_user.user_id,
        expected_holder_name=user.name,
    )


@router.post("/accounts/link", status_code=status.HTTP_201_CREATED)
def link_account(
    payload: LinkAccountRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    return linked_accounts.link_account(
        db,
        current_user.user_id,
        payload.bank_name,
        payload.account_number,
        partner_bank_id=payload.partner_bank_id,
        share_with_partner=payload.share_with_partner,
    )


@router.get("/me/account")
def get_my_linked_account(
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    account = linked_accounts.get_linked_account(db, current_user.user_id)
    return {"account": account}


@router.get("/me/account/simulation")
def get_my_account_simulation(
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    return linked_accounts.get_account_simulation(db, current_user.user_id)
