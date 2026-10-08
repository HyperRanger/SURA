from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal, get_current_principal
from app.database import get_db
from app.schemas import ConsentRequest, ContributionRequest, JoinCommitmentRequest, LockRequest, LockResponse, ReplaceCommitmentMemberRequest
from app.services.commitments import (
    cancel_pending_commitment,
    create_commitment,
    decline_commitment_invitation,
    get_commitment_activity,
    get_commitment_details,
    get_cycle_voucher,
    join_commitment,
    list_member_commitments,
    preview_commitment_by_code,
    record_contribution,
    record_score_consent,
    replace_pending_member,
)

router = APIRouter(prefix="/v1/commitments", tags=["commitments"])
consent_router = APIRouter(prefix="/v1", tags=["commitments"])


def _require_individual(current_user: AuthPrincipal) -> None:
    if current_user.role != "individual":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member access is required.")


@router.post("/lock", response_model=LockResponse, status_code=status.HTTP_201_CREATED)
def create_commitment_lock(
    payload: LockRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    _, response = create_commitment(db, payload, current_user.user_id)
    return response


@router.get("")
def list_my_commitments(
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    return list_member_commitments(db, current_user.user_id)


@router.get("/preview")
def preview_commitment(
    code: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    return preview_commitment_by_code(db, code, current_user.user_id)


@router.post("/join")
def join_commitment_from_invite(
    payload: JoinCommitmentRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    return join_commitment(db, payload.invite_code, current_user.user_id)


@consent_router.post("/consent")
def record_consent(
    payload: ConsentRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    return record_score_consent(db, current_user.user_id, payload.granted)


@router.post("/{commitment_id}/contribute")
def contribute_to_commitment(
    commitment_id: str,
    payload: ContributionRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    return record_contribution(db, commitment_id, current_user.user_id, payload)


@router.post("/{commitment_id}/cancel")
def cancel_commitment(
    commitment_id: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    return cancel_pending_commitment(db, commitment_id, current_user.user_id)


@router.post("/{commitment_id}/decline")
def decline_invitation(
    commitment_id: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    return decline_commitment_invitation(db, commitment_id, current_user.user_id)


@router.post("/{commitment_id}/members/{invited_user_id}/replace")
def replace_invited_member(
    commitment_id: str,
    invited_user_id: str,
    payload: ReplaceCommitmentMemberRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    return replace_pending_member(db, commitment_id, current_user.user_id, invited_user_id, payload.replacement_user_id)


@router.get("/{commitment_id}/activity")
def get_activity(
    commitment_id: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    return get_commitment_activity(db, commitment_id, current_user.user_id)


@router.get("/{commitment_id}/cycles/{cycle_number}/voucher")
def get_voucher(
    commitment_id: str,
    cycle_number: int,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    return get_cycle_voucher(db, commitment_id, cycle_number, current_user.user_id)


@router.get("/{commitment_id}")
def get_commitment(
    commitment_id: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    return get_commitment_details(db, commitment_id, current_user.user_id)
