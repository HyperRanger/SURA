from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal, get_current_principal
from app.database import get_db
from app.schemas import ScoreBreakdown, ScoreResponse
from app.services.score_service import get_score_report

router = APIRouter(prefix="/v1", tags=["score"])


@router.get("/score/{user_id}", response_model=ScoreResponse)
def get_score(
    user_id: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You may only view your own score.")
    report = get_score_report(db, user_id)
    last_updated = report.get("last_updated") or datetime.utcnow()

    return ScoreResponse(
        user_id=user_id,
        score=report["score"],
        tier=report["tier"],
        breakdown=ScoreBreakdown(**report["breakdown"]),
        weights=report["weights"],
        score_version=report["score_version"],
        last_updated=last_updated,
    )
