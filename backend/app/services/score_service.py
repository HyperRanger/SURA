"""Shared database adapter for explainable Sura Score snapshots."""
import json
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any

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
    # Pairwise gaps between consecutive activity. The two sequences are the same
    # list and its own tail, so their lengths differ by one on purpose; this is
    # not a strict zip.
    intervals = tuple((later.occurred_at - earlier.occurred_at).total_seconds() / 86400 for earlier, later in zip(activity, activity[1:], strict=False))
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
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("Cannot record a score for an unknown user.")
    signals = build_score_signals(db, user_id)
    report = build_score_report(signals)
    previous = latest_score_history(db, user_id)
    if previous is not None and previous.score == report["score"]:
        return previous
    snapshot = {**report, "signals": asdict(signals), "event_type": event_type, "reason": reason, "source_id": source_id}
    row = ScoreHistory(id=str(uuid.uuid4()), user_id=user_id, bank_id=user.bank_id, score=report["score"], score_before=previous.score if previous else None, event_type=event_type, reason=reason, source_id=source_id, signals_json=json.dumps(asdict(signals)), breakdown_json=json.dumps(snapshot), score_version=report["score_version"], computed_at=datetime.utcnow())
    db.add(row)
    return row


def get_score_report(db: Session, user_id: str) -> dict:
    latest = latest_score_history(db, user_id)
    if latest and latest.breakdown_json:
        return json.loads(latest.breakdown_json)
    return build_score_report(build_score_signals(db, user_id))


def public_score_report(db: Session, user_id: str) -> dict[str, Any]:
    """The score as consumers see it, free of internal snapshot bookkeeping.

    `get_score_report` returns whatever the stored snapshot carries, which includes
    the raw signals and the event that caused the change. Two callers reading the
    same user's score could therefore get different key sets depending on whether
    the number came from a fresh computation or a stored row. This is the stable
    shape, and it is what the HTTP endpoint and the contribution response both use.
    """
    report = get_score_report(db, user_id)
    latest = latest_score_history(db, user_id)
    return {
        "user_id": user_id,
        "score": report["score"],
        "tier": report["tier"],
        "breakdown": dict(report["breakdown"]),
        "weights": dict(report["weights"]),
        "score_version": report["score_version"],
        "last_updated": (latest.computed_at if latest is not None else None),
    }


def process_contribution(
    db: Session,
    commitment_id: str,
    contributor_user_id: str,
    *,
    event_id: str | None = None,
    reason: str = "contribution_processed",
) -> dict[str, Any]:
    """The single entry point for recomputing Sura Score after a Lock event.

    Callers pass who and what happened. Every input the score depends on is read
    back out of the database, so no caller can hand in a pillar value, a running
    total, or any other claim about a user's behaviour and have it believed. That
    is what keeps the model explainable: the five pillars are a projection of
    recorded commitment events, not an assertion the caller supplies.

    Returns the same shape as `GET /v1/score/{user_id}`.
    """
    if db.get(User, contributor_user_id) is None:
        raise ValueError("Cannot score a contribution for an unknown user.")
    refresh_commitment_member_scores(db, commitment_id, event_id=event_id, reason=reason)
    return public_score_report(db, contributor_user_id)


def refresh_commitment_member_scores(
    db: Session,
    commitment_id: str,
    *,
    event_id: str | None = None,
    reason: str = "contribution_processed",
) -> None:
    commitment = db.get(Commitment, commitment_id)
    if commitment is None:
        return
    members = db.query(CommitmentMember).filter(CommitmentMember.commitment_id == commitment_id).all()
    # Sessions run with autoflush=False, so any beneficiary status the caller just
    # set is still only in memory. Without this flush the paid/missed counts below
    # read the database as it was before this event and silently drop the
    # cycle-completion bonus from the score.
    db.flush()
    for member in members:
        if member.role != "invited":
            record_score_snapshot(
                db,
                member.user_id,
                event_type="contribution_processed",
                reason=reason,
                source_id=event_id or commitment_id,
            )
    # The snapshots above are only added, not written. Sessions here run with
    # autoflush=False, so a caller that immediately reads the score back would see
    # the previous value and a null `last_updated` for a score it just changed.
    db.flush()
