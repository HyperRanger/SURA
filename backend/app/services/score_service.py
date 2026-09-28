"""Shared database adapter for explainable Sura Score snapshots."""
import json
import uuid
from dataclasses import asdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import AccountActivitySignal, Commitment, CommitmentBeneficiary, CommitmentMember, Contribution, ScoreHistory, User
from app.services.scoring import ScoreSignals, build_score_report


def build_score_signals(db: Session, user_id: str) -> ScoreSignals:
    user = db.get(User, user_id)
    if user is None:
        return ScoreSignals()
    memberships = db.query(CommitmentMember).filter(CommitmentMember.user_id == user_id, CommitmentMember.role != "invited").all()
    commitment_ids = [row.commitment_id for row in memberships]
    commitments = db.query(Commitment).filter(Commitment.id.in_(commitment_ids)).all() if commitment_ids else []
    closed = db.query(CommitmentBeneficiary).filter(CommitmentBeneficiary.commitment_id.in_(commitment_ids), CommitmentBeneficiary.status.in_(("paid", "redeemed", "missed"))).all() if commitment_ids else []
    due = {(row.commitment_id, row.cycle_number) for row in closed}
    expected = {row.id: row.contribution_amount for row in commitments}
    paid: dict[tuple[str, int], int] = {}
    for row in (db.query(Contribution).filter(Contribution.user_id == user_id, Contribution.commitment_id.in_(commitment_ids)).all() if commitment_ids else []):
        key = (row.commitment_id, row.cycle_number)
        paid[key] = paid.get(key, 0) + row.amount
    activity = db.query(AccountActivitySignal).filter(AccountActivitySignal.user_id == user_id).order_by(AccountActivitySignal.occurred_at).all()
    intervals = tuple((later.occurred_at - earlier.occurred_at).total_seconds() / 86400 for earlier, later in zip(activity, activity[1:]))
    cosigners = db.query(CommitmentMember).join(User, User.id == CommitmentMember.user_id).filter(CommitmentMember.commitment_id.in_(commitment_ids), CommitmentMember.user_id != user_id, CommitmentMember.role != "invited", User.verified_at.is_not(None)).count() if commitment_ids else 0
    return ScoreSignals(
        locks_joined=len(commitment_ids),
        locks_completed=sum(1 for row in commitments if row.status == "completed"),
        contributions_due=len(due),
        contributions_on_time=sum(1 for key in due if paid.get(key, 0) >= expected[key[0]]),
        activity_intervals_days=intervals,
        institution_verified=user.verified_at is not None,
        cosigners=cosigners,
    )


def latest_score_history(db: Session, user_id: str) -> ScoreHistory | None:
    return db.query(ScoreHistory).filter(ScoreHistory.user_id == user_id).order_by(ScoreHistory.computed_at.desc(), ScoreHistory.id.desc()).first()


def record_score_snapshot(db: Session, user_id: str, *, event_type: str, reason: str, source_id: str | None = None) -> ScoreHistory:
    signals = build_score_signals(db, user_id)
    report = build_score_report(signals)
    previous = latest_score_history(db, user_id)
    snapshot = {**report, "signals": asdict(signals), "event_type": event_type, "reason": reason, "source_id": source_id}
    row = ScoreHistory(id=str(uuid.uuid4()), user_id=user_id, score=report["score"], score_before=previous.score if previous else None, event_type=event_type, reason=reason, source_id=source_id, signals_json=json.dumps(asdict(signals)), breakdown_json=json.dumps(snapshot), score_version=report["score_version"], computed_at=datetime.utcnow())
    db.add(row)
    return row


def get_score_report(db: Session, user_id: str) -> dict:
    latest = latest_score_history(db, user_id)
    if latest and latest.breakdown_json:
        return json.loads(latest.breakdown_json)
    return build_score_report(build_score_signals(db, user_id))
