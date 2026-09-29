"""HTTP contract consumed by the Bank Portal frontend."""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal
from app.bank.dependencies import require_bank_permission
from app.bank import service
from app.database import get_db


class FlagResolutionRequest(BaseModel):
    action: str = Field(pattern="^(dismissed|confirmed|escalated)$")
    note: str = Field(min_length=1, max_length=1000)


router = APIRouter(prefix="/v1/bank", tags=["bank portal"])


@router.get("/overview")
def bank_overview(
    current: AuthPrincipal = Depends(require_bank_permission("bank:overview:read")),
    db: Session = Depends(get_db),
):
    return service.overview(db, current.institution_id)


@router.get("/users")
def bank_users(
    q: str | None = Query(default=None, description="Name, phone, Sura user ID, bank customer reference, or commitment ID."),
    bank_customer_id: str | None = Query(default=None, description="Exact authorised bank customer reference."),
    score_tier: str | None = Query(default=None, description="Score tier: unverified, entry, building, or established."),
    flag_status: str | None = Query(default=None, description="Return customers with a flag in this status."),
    current: AuthPrincipal = Depends(require_bank_permission("bank:users:read")),
    db: Session = Depends(get_db),
):
    return service.list_users(
        db,
        current.institution_id,
        query=q,
        bank_customer_id=bank_customer_id,
        score_tier=score_tier,
        flag_status=flag_status,
    )


@router.get("/users/{user_id}")
def bank_user_profile(
    user_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:users:read")),
    db: Session = Depends(get_db),
):
    response = service.get_user_profile(db, current.institution_id, current.user_id, user_id)
    db.commit()
    return response


@router.get("/users/{user_id}/score")
def bank_user_score(
    user_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:users:read")),
    db: Session = Depends(get_db),
):
    response = service.get_user_score(db, current.institution_id, current.user_id, user_id)
    db.commit()
    return response


@router.get("/users/{user_id}/commitments")
def bank_user_commitments(
    user_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:users:read")),
    db: Session = Depends(get_db),
):
    return service.get_user_commitments(db, current.institution_id, user_id)


@router.get("/users/{user_id}/activity")
def bank_user_activity(
    user_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:users:read")),
    db: Session = Depends(get_db),
):
    return service.get_user_activity(db, current.institution_id, user_id)


@router.get("/users/{user_id}/flags")
def bank_user_flags(
    user_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:flags:read")),
    db: Session = Depends(get_db),
):
    service._user_or_404(db, current.institution_id, user_id)
    return service.list_flags(db, current.institution_id, user_id)


@router.get("/commitments")
def bank_commitments(
    current: AuthPrincipal = Depends(require_bank_permission("bank:commitments:read")),
    db: Session = Depends(get_db),
):
    return service.list_commitments(db, current.institution_id)


@router.get("/commitments/{commitment_id}")
def bank_commitment(
    commitment_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:commitments:read")),
    db: Session = Depends(get_db),
):
    return service.get_commitment(db, current.institution_id, commitment_id)


@router.get("/audit-log")
def bank_audit_log(
    current: AuthPrincipal = Depends(require_bank_permission("bank:audit:read")),
    db: Session = Depends(get_db),
):
    return service.audit_log(db, current.institution_id)


@router.get("/flags")
def bank_flags(
    current: AuthPrincipal = Depends(require_bank_permission("bank:flags:read")),
    db: Session = Depends(get_db),
):
    return service.list_flags(db, current.institution_id)


@router.post("/flags/{flag_id}/resolve")
def bank_resolve_flag(
    flag_id: str,
    payload: FlagResolutionRequest,
    current: AuthPrincipal = Depends(require_bank_permission("bank:flags:write")),
    db: Session = Depends(get_db),
):
    return service.resolve_flag(db, current.institution_id, current.user_id, flag_id, payload.action, payload.note)


@router.get("/settlements")
def bank_settlements(
    current: AuthPrincipal = Depends(require_bank_permission("bank:settlements:read")),
    db: Session = Depends(get_db),
):
    return service.settlements(db, current.institution_id)
