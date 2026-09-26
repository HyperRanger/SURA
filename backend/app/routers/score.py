from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ScoreBreakdown, ScoreResponse

router = APIRouter(prefix="/v1", tags=["score"])


@router.get("/score/{user_id}", response_model=ScoreResponse)
def get_score(user_id: str, db: Session = Depends(get_db)):
    return ScoreResponse(
        user_id=user_id,
        score=70,
        breakdown=ScoreBreakdown(
            commitment_behaviour=0.35,
            repayment_behaviour=0.25,
            transaction_stability=0.20,
            institutional_verification=0.12,
            social_reliability=0.08,
        ),
        last_updated=datetime.utcnow(),
    )
