from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal, get_current_principal
from app.database import get_db
from app.models import ScoreHistory
from app.schemas import ScoreBreakdown, ScoreHistoryEntry, ScoreHistoryResponse, ScoreResponse
from app.services.score_service import public_score_report, serialize_score_history_entry

router = APIRouter(prefix="/v1", tags=["score"])


@router.get("/score/{user_id}", response_model=ScoreResponse)
def get_score(
    user_id: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    if current_user.role != "individual":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member access is required.")
    if current_user.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You may only view your own score.")
    report = public_score_report(db, user_id)
    # A user with no recorded change has no snapshot time. The schema requires a
    # datetime, so the read itself is the most recent thing that happened to it.
    last_updated = report["last_updated"] or datetime.now(timezone.utc)

    return ScoreResponse(
        user_id=user_id,
        score=report["score"],
        tier=report["tier"],
        breakdown=ScoreBreakdown(**report["breakdown"]),
        weights=report["weights"],
        score_version=report["score_version"],
        last_updated=last_updated,
    )


@router.get("/score/{user_id}/history", response_model=ScoreHistoryResponse)
def get_score_history(
    user_id: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Every recorded score change for a user, newest first.

    A bank cannot underwrite on a number it cannot explain, so this returns the
    full paper trail behind the current score: the score before and after each
    change, the event that caused it, and the weighted breakdown.
    """
    if current_user.role != "individual":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member access is required.")
    if current_user.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You may only view your own score history.")
    rows = (
        db.query(ScoreHistory)
        .filter(ScoreHistory.user_id == user_id)
        .order_by(ScoreHistory.computed_at.desc(), ScoreHistory.id.desc())
        .all()
    )

    entries = [
        ScoreHistoryEntry(
            **{
                **serialize_score_history_entry(row),
                "computed_at": row.computed_at or datetime.utcnow(),
            }
        )
        for row in rows
    ]

    return ScoreHistoryResponse(
        user_id=user_id,
        current_score=entries[0].score if entries else public_score_report(db, user_id)["score"],
        entries=entries,
    )


@router.get("/score/{user_id}/history/{entry_id}", response_model=ScoreHistoryEntry)
def get_score_history_entry(
    user_id: str,
    entry_id: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Return one immutable, explainable Score snapshot to its owner."""
    if current_user.role != "individual":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member access is required.")
    if current_user.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You may only view your own score history.")
    row = db.query(ScoreHistory).filter(ScoreHistory.id == entry_id, ScoreHistory.user_id == user_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Score history entry not found.")
    return ScoreHistoryEntry(**{**serialize_score_history_entry(row), "computed_at": row.computed_at or datetime.utcnow()})
