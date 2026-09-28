import json
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal, get_current_principal
from app.database import get_db
from app.models import ScoreHistory
from app.schemas import ScoreBreakdown, ScoreHistoryEntry, ScoreHistoryResponse, ScoreResponse
from app.services.scoring import score_breakdown

router = APIRouter(prefix="/v1", tags=["score"])


@router.get("/score/{user_id}", response_model=ScoreResponse)
def get_score(
    user_id: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    latest = (
        db.query(ScoreHistory)
        .filter(ScoreHistory.user_id == user_id)
        .order_by(ScoreHistory.computed_at.desc(), ScoreHistory.id.desc())
        .first()
    )

    breakdown_payload = score_breakdown()
    score = 12
    last_updated = datetime.utcnow()
    if latest is not None:
        score = latest.score
        last_updated = latest.computed_at or last_updated
        if latest.breakdown_json:
            stored_snapshot = json.loads(latest.breakdown_json)
            breakdown_payload = stored_snapshot.get("breakdown", stored_snapshot)

    return ScoreResponse(
        user_id=user_id,
        score=score,
        breakdown=ScoreBreakdown(**breakdown_payload),
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
    rows = (
        db.query(ScoreHistory)
        .filter(ScoreHistory.user_id == user_id)
        .order_by(ScoreHistory.computed_at.desc(), ScoreHistory.id.desc())
        .all()
    )

    entries: list[ScoreHistoryEntry] = []
    for row in rows:
        breakdown = None
        if row.breakdown_json:
            stored = json.loads(row.breakdown_json)
            breakdown_payload = stored.get("breakdown", stored)
            breakdown = ScoreBreakdown(**breakdown_payload)
        entries.append(
            ScoreHistoryEntry(
                score=row.score,
                old_score=row.old_score,
                event_id=row.event_id,
                reason=row.reason,
                computed_at=row.computed_at or datetime.utcnow(),
                breakdown=breakdown,
            )
        )

    return ScoreHistoryResponse(
        user_id=user_id,
        current_score=entries[0].score if entries else 12,
        entries=entries,
    )
