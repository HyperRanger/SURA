import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ContributionRequest, LockRequest, LockResponse, PayoutScheduleItem

router = APIRouter(prefix="/v1/commitments", tags=["commitments"])


@router.post("/lock", response_model=LockResponse, status_code=status.HTTP_201_CREATED)
def create_commitment_lock(payload: LockRequest, db: Session = Depends(get_db)):
    commitment_id = str(uuid.uuid4())

    if not payload.members:
        raise HTTPException(status_code=400, detail="At least one member is required.")

    payout_schedule = [
        PayoutScheduleItem(cycle=1, beneficiary_id=payload.members[0], amount=payload.contribution_amount)
    ]

    return LockResponse(
        commitment_id=commitment_id,
        type=payload.type,
        status="pending_members",
        invite_code="SURA-" + str(uuid.uuid4())[:8].upper(),
        payout_schedule=payout_schedule,
    )


@router.post("/{commitment_id}/contribute")
def contribute_to_commitment(commitment_id: str, payload: ContributionRequest, db: Session = Depends(get_db)):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Contribution amount must be positive.")

    return {
        "commitment_id": commitment_id,
        "user_id": payload.user_id,
        "amount": payload.amount,
        "status": "active",
        "message": "Contribution recorded successfully.",
        "completed_cycle": False,
        "beneficiary": None,
        "updated_at": datetime.utcnow().isoformat(),
    }


@router.get("/{commitment_id}")
def get_commitment(commitment_id: str, db: Session = Depends(get_db)):
    return {
        "commitment_id": commitment_id,
        "status": "pending_members",
        "members": [],
        "beneficiaries": [],
        "cycles": [],
    }
