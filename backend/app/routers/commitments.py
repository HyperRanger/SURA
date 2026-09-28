from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal, get_current_principal
from app.database import get_db
from app.schemas import ConsentRequest, ContributionRequest, JoinCommitmentRequest, LockRequest, LockResponse
from app.services.commitments import (
    cancel_pending_commitment,
    create_commitment,
    get_commitment_activity,
    get_commitment_details,
    get_cycle_voucher,
    join_commitment,
    list_member_commitments,
    preview_commitment_by_code,
    record_contribution,
    record_score_consent,
)

router = APIRouter(prefix="/v1/commitments", tags=["commitments"])


@router.post("/lock", response_model=LockResponse, status_code=status.HTTP_201_CREATED)
def create_commitment_lock(
    payload: LockRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _, response = create_commitment(db, payload, current_user.user_id)
    return response


@router.get("")
def list_my_commitments(
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    return list_member_commitments(db, current_user.user_id)


@router.get("/preview")
def preview_commitment(
    code: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    return preview_commitment_by_code(db, code, current_user.user_id)


@router.post("/join")
def join_commitment_from_invite(
    payload: JoinCommitmentRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    return join_commitment(db, payload.invite_code, current_user.user_id)


@router.post("/consent")
def record_consent(
    payload: ConsentRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    return record_score_consent(db, current_user.user_id, payload.granted)


@router.post("/{commitment_id}/contribute")
def contribute_to_commitment(
    commitment_id: str,
    payload: ContributionRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    return record_contribution(db, commitment_id, current_user.user_id, payload)


@router.post("/{commitment_id}/cancel")
def cancel_commitment(
    commitment_id: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    return cancel_pending_commitment(db, commitment_id, current_user.user_id)


@router.get("/{commitment_id}/activity")
def get_activity(
    commitment_id: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    return get_commitment_activity(db, commitment_id, current_user.user_id)


@router.get("/{commitment_id}/cycles/{cycle_number}/voucher")
def get_voucher(
    commitment_id: str,
    cycle_number: int,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    return get_cycle_voucher(db, commitment_id, cycle_number, current_user.user_id)


@router.get("/{commitment_id}")
def get_commitment(
    commitment_id: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    return get_commitment_details(db, commitment_id, current_user.user_id)
