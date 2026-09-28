"""Bank-scoped read models and risk-flag actions for the Bank Portal."""

import json
import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.bank.models import BankAuditEvent, RiskFlag
from app.models import Commitment, CommitmentActivity, CommitmentMember, Contribution, Redemption, ScoreHistory, User
from app.services.score_service import get_score_report, latest_score_history


def _masked(value: str | None) -> str | None:
    if not value:
        return None
    return "•" * max(0, len(value) - 4) + value[-4:]


def _audit(db: Session, bank_id: str, actor_id: str, event_type: str, subject_type: str, subject_id: str, details: dict | None = None) -> None:
    db.add(BankAuditEvent(
        id=str(uuid.uuid4()), bank_id=bank_id, actor_id=actor_id, event_type=event_type,
        subject_type=subject_type, subject_id=subject_id, detail_json=json.dumps(details or {}), occurred_at=datetime.utcnow(),
    ))


def _user_or_404(db: Session, bank_id: str, user_id: str) -> User:
    user = db.query(User).filter(User.id == user_id, User.bank_id == bank_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Customer not found for this bank.")
    return user


def _user_summary(db: Session, user: User) -> dict:
    score = get_score_report(db, user.id)
    memberships = db.query(CommitmentMember).filter(CommitmentMember.user_id == user.id, CommitmentMember.role != "invited").count()
    active = db.query(Commitment).join(CommitmentMember).filter(CommitmentMember.user_id == user.id, Commitment.status == "active").count()
    open_flags = db.query(RiskFlag).filter(RiskFlag.user_id == user.id, RiskFlag.bank_id == user.bank_id, RiskFlag.status == "open").count()
    return {
        "user_id": user.id,
        "name": user.name,
        "phone": _masked(user.phone),
        "bank_customer_id": _masked(user.bank_customer_id),
        "verified": user.verified_at is not None,
        "score": score["score"],
        "tier": score["tier"],
        "commitments_joined": memberships,
        "active_commitments": active,
        "open_flags": open_flags,
    }


def list_users(db: Session, bank_id: str, query: str | None = None) -> list[dict]:
    users = db.query(User).filter(User.bank_id == bank_id)
    if query:
        token = f"%{query.strip()}%"
        users = users.outerjoin(CommitmentMember, CommitmentMember.user_id == User.id).filter(or_(
            User.id.ilike(token), User.name.ilike(token), User.phone.ilike(token),
            User.bank_customer_id.ilike(token), CommitmentMember.commitment_id.ilike(token),
        )).distinct()
    return [_user_summary(db, user) for user in users.order_by(User.name.asc(), User.id.asc()).all()]


def get_user_profile(db: Session, bank_id: str, actor_id: str, user_id: str) -> dict:
    user = _user_or_404(db, bank_id, user_id)
    _audit(db, bank_id, actor_id, "customer_profile_viewed", "user", user_id)
    profile = _user_summary(db, user)
    report = get_score_report(db, user.id)
    profile.update({
        "score_report": report,
        "float_eligibility": "eligible" if report["score"] > 120 else "locked",
        "float_eligibility_reason": "Float is not part of this MVP." if report["score"] > 120 else "Complete a Sura Lock before Float can unlock.",
    })
    return profile


def get_user_score(db: Session, bank_id: str, actor_id: str, user_id: str) -> dict:
    _user_or_404(db, bank_id, user_id)
    _audit(db, bank_id, actor_id, "customer_score_viewed", "user", user_id)
    report = get_score_report(db, user_id)
    history = db.query(ScoreHistory).filter(ScoreHistory.user_id == user_id).order_by(ScoreHistory.computed_at.desc(), ScoreHistory.id.desc()).all()
    return {
        "user_id": user_id,
        "current": report,
        "history": [{
            "id": row.id, "score": row.score, "score_before": row.score_before, "event_type": row.event_type,
            "reason": row.reason, "source_id": row.source_id, "score_version": row.score_version,
            "computed_at": row.computed_at.isoformat() if row.computed_at else None,
            "breakdown": json.loads(row.breakdown_json).get("breakdown", {}),
        } for row in history],
    }


def get_user_commitments(db: Session, bank_id: str, user_id: str) -> list[dict]:
    _user_or_404(db, bank_id, user_id)
    rows = db.query(Commitment).join(CommitmentMember).filter(CommitmentMember.user_id == user_id).order_by(Commitment.created_at.desc()).all()
    return [{
        "commitment_id": row.id, "title": row.title, "status": row.status, "type": row.type,
        "vendor_id": row.vendor_id, "contribution_amount": row.contribution_amount, "cycles": row.cycles,
        "completed_cycle_count": row.completed_cycle_count, "created_at": row.created_at.isoformat() if row.created_at else None,
    } for row in rows]


def get_user_activity(db: Session, bank_id: str, user_id: str) -> list[dict]:
    _user_or_404(db, bank_id, user_id)
    score_events = db.query(ScoreHistory).filter(ScoreHistory.user_id == user_id).all()
    commitment_events = db.query(CommitmentActivity).join(CommitmentMember, CommitmentMember.commitment_id == CommitmentActivity.commitment_id).filter(CommitmentMember.user_id == user_id).all()
    events = [{"type": "score_updated", "id": row.id, "reason": row.reason, "occurred_at": row.computed_at} for row in score_events]
    events.extend({"type": row.event_type, "id": row.id, "details": json.loads(row.detail_json), "occurred_at": row.occurred_at} for row in commitment_events)
    return [{**row, "occurred_at": row["occurred_at"].isoformat() if row["occurred_at"] else None} for row in sorted(events, key=lambda item: item["occurred_at"] or datetime.min, reverse=True)]


def list_commitments(db: Session, bank_id: str) -> list[dict]:
    rows = db.query(Commitment).join(CommitmentMember).join(User, User.id == CommitmentMember.user_id).filter(User.bank_id == bank_id).distinct().order_by(Commitment.created_at.desc()).all()
    return [{"commitment_id": row.id, "title": row.title, "status": row.status, "vendor_id": row.vendor_id, "cycles": row.cycles, "completed_cycle_count": row.completed_cycle_count} for row in rows]


def get_commitment(db: Session, bank_id: str, commitment_id: str) -> dict:
    if not db.query(CommitmentMember).join(User, User.id == CommitmentMember.user_id).filter(CommitmentMember.commitment_id == commitment_id, User.bank_id == bank_id).first():
        raise HTTPException(status_code=404, detail="Commitment not found for this bank.")
    row = db.get(Commitment, commitment_id)
    return {"commitment_id": row.id, "title": row.title, "status": row.status, "vendor_id": row.vendor_id, "cycles": row.cycles, "completed_cycle_count": row.completed_cycle_count}


def overview(db: Session, bank_id: str) -> dict:
    commitments = list_commitments(db, bank_id)
    customer_count = db.query(User).filter(User.bank_id == bank_id).count()
    contribution_total = db.query(func.coalesce(func.sum(Contribution.amount), 0)).join(User, User.id == Contribution.user_id).filter(User.bank_id == bank_id).scalar()
    return {
        "customers": customer_count,
        "active_commitments": sum(1 for row in commitments if row["status"] == "active"),
        "total_contributed": int(contribution_total or 0),
        "completion_rate": round(sum(1 for row in commitments if row["status"] == "completed") / len(commitments), 2) if commitments else 0,
        "open_flags": db.query(RiskFlag).filter(RiskFlag.bank_id == bank_id, RiskFlag.status == "open").count(),
    }


def audit_log(db: Session, bank_id: str) -> list[dict]:
    scores = db.query(ScoreHistory).join(User, User.id == ScoreHistory.user_id).filter(User.bank_id == bank_id).all()
    access = db.query(BankAuditEvent).filter(BankAuditEvent.bank_id == bank_id).all()
    events = [{"type": "score", "id": row.id, "user_id": row.user_id, "event_type": row.event_type, "reason": row.reason, "occurred_at": row.computed_at} for row in scores]
    events.extend({"type": "bank_access", "id": row.id, "actor_id": row.actor_id, "event_type": row.event_type, "subject_id": row.subject_id, "occurred_at": row.occurred_at} for row in access)
    return [{**event, "occurred_at": event["occurred_at"].isoformat() if event["occurred_at"] else None} for event in sorted(events, key=lambda item: item["occurred_at"] or datetime.min, reverse=True)]


def list_flags(db: Session, bank_id: str, user_id: str | None = None) -> list[dict]:
    rows = db.query(RiskFlag).filter(RiskFlag.bank_id == bank_id)
    if user_id:
        rows = rows.filter(RiskFlag.user_id == user_id)
    return [_serialize_flag(row) for row in rows.order_by(RiskFlag.created_at.desc()).all()]


def _serialize_flag(row: RiskFlag) -> dict:
    return {"flag_id": row.id, "user_id": row.user_id, "rule": row.rule, "severity": row.severity, "status": row.status, "evidence": json.loads(row.evidence_json), "resolution_note": row.resolution_note, "created_at": row.created_at.isoformat() if row.created_at else None, "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None}


def resolve_flag(db: Session, bank_id: str, actor_id: str, flag_id: str, action: str, note: str) -> dict:
    if action not in {"dismissed", "confirmed", "escalated"}:
        raise HTTPException(status_code=400, detail="Flag action must be dismissed, confirmed, or escalated.")
    row = db.query(RiskFlag).filter(RiskFlag.id == flag_id, RiskFlag.bank_id == bank_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Risk flag not found.")
    row.status, row.resolution_note, row.resolved_by, row.resolved_at = action, note, actor_id, datetime.utcnow()
    _audit(db, bank_id, actor_id, "risk_flag_resolved", "risk_flag", flag_id, {"action": action})
    db.commit()
    return _serialize_flag(row)


def settlements(db: Session, bank_id: str) -> list[dict]:
    rows = db.query(Redemption).join(User, User.id == Redemption.beneficiary_id).filter(User.bank_id == bank_id).order_by(Redemption.redeemed_at.desc()).all()
    return [{"settlement_id": row.id, "commitment_id": row.commitment_id, "vendor_id": row.vendor_id, "amount": row.amount, "voucher_code": row.voucher_code, "status": row.status, "redeemed_at": row.redeemed_at.isoformat() if row.redeemed_at else None, "simulated": True} for row in rows]
