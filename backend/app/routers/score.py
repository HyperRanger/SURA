import json
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ScoreHistory
from app.schemas import ScoreBreakdown, ScoreResponse
from app.services.scoring import score_breakdown

router = APIRouter(prefix="/v1", tags=["score"])


@router.get("/score/{user_id}", response_model=ScoreResponse)
def get_score(user_id: str, db: Session = Depends(get_db)):
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
