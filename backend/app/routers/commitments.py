from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal, get_current_principal
from app.database import get_db
from app.schemas import ContributionRequest, LockRequest, LockResponse
from app.services.commitments import create_commitment, get_commitment_details, record_contribution, redeem_cycle

router = APIRouter(prefix="/v1/commitments", tags=["commitments"])


@router.post("/lock", response_model=LockResponse, status_code=status.HTTP_201_CREATED)
def create_commitment_lock(
    payload: LockRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _, response = create_commitment(db, payload, current_user.user_id)
    return response


@router.post("/{commitment_id}/contribute")
def contribute_to_commitment(
    commitment_id: str,
    payload: ContributionRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    return record_contribution(db, commitment_id, current_user.user_id, payload)


@router.post("/{commitment_id}/redeem")
def redeem_commitment_cycle(
    commitment_id: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    return redeem_cycle(db, commitment_id, current_user.user_id)


@router.get("/{commitment_id}")
def get_commitment(
    commitment_id: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    return get_commitment_details(db, commitment_id)
