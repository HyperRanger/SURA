"""Bank-scoped read models and risk-flag actions for the Bank Portal."""

import csv
import io
import json
import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.bank import risk_rules
from app.bank.models import BankAuditEvent, BankPartner, BankStaff, RiskFlag
from app.models import (
    Commitment,
    CommitmentActivity,
    CommitmentBeneficiary,
    CommitmentCase,
    CommitmentMember,
    Contribution,
    Institution,
    Redemption,
    ScoreHistory,
    User,
    UserConsent,
    Vendor,
    Voucher,
)
from app.services import audit
from app.services.commitments import refresh_commitment_lifecycle
from app.services.score_service import get_score_report, public_score_report, serialize_score_history_entry

SCORE_TIERS = frozenset({"unverified", "entry", "building", "established"})
FLAG_STATUSES = frozenset({"open", "dismissed", "confirmed", "escalated"})


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
    # Bank staff authenticate through user records, but they are never bank
    # customers and must not be visible in customer search or score views.
    user = (
        db.query(User)
        .outerjoin(BankStaff, BankStaff.user_id == User.id)
        .filter(User.id == user_id, User.bank_id == bank_id, BankStaff.id.is_(None))
        .one_or_none()
    )
    if user is None:
        raise HTTPException(status_code=404, detail="Customer not found for this bank.")
    return user


def _user_summary(db: Session, user: User) -> dict:
    score = get_score_report(db, user.id)
    source_institution = db.get(Institution, user.institution_id) if user.institution_id else None
    memberships = db.query(CommitmentMember).filter(CommitmentMember.user_id == user.id, CommitmentMember.role != "invited").count()
    active = db.query(Commitment).join(CommitmentMember).filter(CommitmentMember.user_id == user.id, Commitment.status == "active").count()
    open_flags = db.query(RiskFlag).filter(RiskFlag.user_id == user.id, RiskFlag.bank_id == user.bank_id, RiskFlag.status == "open").count()
    contributions = db.query(Contribution).filter(Contribution.user_id == user.id).all()
    on_time_rate = round(sum(1 for contribution in contributions if contribution.status == "full") / len(contributions), 2) if contributions else None
    return {
        "user_id": user.id,
        "name": user.name,
        "phone": _masked(user.phone),
        "account_status": user.account_status,
        "restriction_reason": user.restriction_reason,
        "bank_customer_id": _masked(user.bank_customer_id),
        # This is where a member banks outside the Sura integration tenancy.
        # It is descriptive portfolio context only; it never changes access.
        "source_institution": (
            {"institution_id": source_institution.id, "name": source_institution.name}
            if source_institution is not None
            else None
        ),
        "available_balance": user.available_balance,
        "verified": user.verified_at is not None,
        "score": score["score"],
        "tier": score["tier"],
        "commitments_joined": memberships,
        "active_commitments": active,
        "open_flags": open_flags,
        "on_time_contribution_rate": on_time_rate,
        "float_eligibility": "eligible" if score["score"] > 120 else "locked",
    }


def _user_summaries(db: Session, users: list[User]) -> list[dict]:
    """Build Bank Portal search rows in a fixed number of database queries.

    The customer directory used to call ``_user_summary`` once per customer.
    Each call has its own score, membership, flag, contribution, and institution
    queries, so a 70-customer portfolio became hundreds of database round trips.
    Search reads immutable Score snapshots, then batches the remaining aggregates.
    A legacy user with no snapshot falls back to the established score service.
    """
    if not users:
        return []

    user_ids = [user.id for user in users]
    institution_ids = {user.institution_id for user in users if user.institution_id}
    institutions_by_id = {
        row.id: row
        for row in db.query(Institution).filter(Institution.id.in_(institution_ids)).all()
    } if institution_ids else {}

    ranked_scores = (
        db.query(
            ScoreHistory.user_id.label("user_id"),
            ScoreHistory.score.label("score"),
            ScoreHistory.breakdown_json.label("breakdown_json"),
            func.row_number().over(
                partition_by=ScoreHistory.user_id,
                order_by=(ScoreHistory.computed_at.desc(), ScoreHistory.id.desc()),
            ).label("position"),
        )
        .filter(ScoreHistory.user_id.in_(user_ids))
        .subquery()
    )
    snapshot_by_user = {
        row.user_id: row
        for row in db.query(ranked_scores).filter(ranked_scores.c.position == 1).all()
    }

    membership_counts = dict(
        db.query(CommitmentMember.user_id, func.count(CommitmentMember.user_id))
        .filter(
            CommitmentMember.user_id.in_(user_ids),
            CommitmentMember.role != "invited",
        )
        .group_by(CommitmentMember.user_id)
        .all()
    )
    active_counts = dict(
        db.query(CommitmentMember.user_id, func.count(CommitmentMember.user_id))
        .join(Commitment, Commitment.id == CommitmentMember.commitment_id)
        .filter(
            CommitmentMember.user_id.in_(user_ids),
            Commitment.status == "active",
        )
        .group_by(CommitmentMember.user_id)
        .all()
    )
    bank_ids = {user.bank_id for user in users if user.bank_id}
    open_flags = {
        (row.bank_id, row.user_id): row.count
        for row in (
            db.query(
                RiskFlag.bank_id,
                RiskFlag.user_id,
                func.count(RiskFlag.id).label("count"),
            )
            .filter(
                RiskFlag.user_id.in_(user_ids),
                RiskFlag.bank_id.in_(bank_ids),
                RiskFlag.status == "open",
            )
            .group_by(RiskFlag.bank_id, RiskFlag.user_id)
            .all()
            if bank_ids
            else []
        )
    }
    contribution_stats = {
        row.user_id: (int(row.total or 0), int(row.full or 0))
        for row in (
            db.query(
                Contribution.user_id.label("user_id"),
                func.count(Contribution.id).label("total"),
                func.sum(case((Contribution.status == "full", 1), else_=0)).label("full"),
            )
            .filter(Contribution.user_id.in_(user_ids))
            .group_by(Contribution.user_id)
            .all()
        )
    }

    summaries: list[dict] = []
    for user in users:
        snapshot = snapshot_by_user.get(user.id)
        if snapshot is not None and snapshot.breakdown_json:
            report = json.loads(snapshot.breakdown_json)
            score = int(report.get("score", snapshot.score))
            tier = report.get("tier", "unverified")
        else:
            # This is only for data predating Score history. Once it is viewed,
            # the normal score lifecycle creates a snapshot for subsequent reads.
            report = get_score_report(db, user.id)
            score = report["score"]
            tier = report["tier"]
        total_contributions, full_contributions = contribution_stats.get(user.id, (0, 0))
        source_institution = institutions_by_id.get(user.institution_id)
        summaries.append({
            "user_id": user.id,
            "name": user.name,
            "phone": _masked(user.phone),
            "account_status": user.account_status,
            "restriction_reason": user.restriction_reason,
            "bank_customer_id": _masked(user.bank_customer_id),
            "source_institution": (
                {"institution_id": source_institution.id, "name": source_institution.name}
                if source_institution is not None
                else None
            ),
            "available_balance": user.available_balance,
            "verified": user.verified_at is not None,
            "score": score,
            "tier": tier,
            "commitments_joined": int(membership_counts.get(user.id, 0)),
            "active_commitments": int(active_counts.get(user.id, 0)),
            "open_flags": int(open_flags.get((user.bank_id, user.id), 0)),
            "on_time_contribution_rate": (
                round(full_contributions / total_contributions, 2)
                if total_contributions
                else None
            ),
            "float_eligibility": "eligible" if score > 120 else "locked",
        })
    return summaries


def list_users(
    db: Session,
    bank_id: str,
    query: str | None = None,
    bank_customer_id: str | None = None,
    score_tier: str | None = None,
    flag_status: str | None = None,
    verified: bool | None = None,
    float_eligibility: str | None = None,
    commitment_status: str | None = None,
) -> list[dict]:
    if score_tier is not None and score_tier not in SCORE_TIERS:
        raise HTTPException(status_code=400, detail="Unknown score tier.")
    if flag_status is not None and flag_status not in FLAG_STATUSES:
        raise HTTPException(status_code=400, detail="Unknown flag status.")
    if float_eligibility is not None and float_eligibility not in {"eligible", "locked"}:
        raise HTTPException(status_code=400, detail="Unknown Float eligibility state.")

    users = (
        db.query(User)
        .outerjoin(BankStaff, BankStaff.user_id == User.id)
        .filter(User.bank_id == bank_id, BankStaff.id.is_(None))
    )
    if bank_customer_id:
        users = users.filter(User.bank_customer_id == bank_customer_id.strip())
    if query:
        token = f"%{query.strip()}%"
        users = users.outerjoin(CommitmentMember, CommitmentMember.user_id == User.id).filter(or_(
            User.id.ilike(token), User.name.ilike(token), User.phone.ilike(token),
            User.bank_customer_id.ilike(token), CommitmentMember.commitment_id.ilike(token),
        )).distinct()
    if verified is not None:
        users = users.filter(User.verified_at.is_not(None) if verified else User.verified_at.is_(None))
    summaries = _user_summaries(db, users.order_by(User.name.asc(), User.id.asc()).all())
    if score_tier is not None:
        summaries = [summary for summary in summaries if summary["tier"] == score_tier]
    if flag_status is not None:
        matching_user_ids = {
            row.user_id
            for row in db.query(RiskFlag.user_id)
            .filter(RiskFlag.bank_id == bank_id, RiskFlag.status == flag_status)
            .all()
        }
        summaries = [summary for summary in summaries if summary["user_id"] in matching_user_ids]
    if float_eligibility is not None:
        summaries = [summary for summary in summaries if ("eligible" if summary["score"] > 120 else "locked") == float_eligibility]
    if commitment_status is not None:
        matching_user_ids = {
            row.user_id for row in db.query(CommitmentMember.user_id).join(Commitment).filter(Commitment.status == commitment_status).all()
        }
        summaries = [summary for summary in summaries if summary["user_id"] in matching_user_ids]
    return summaries


def get_user_profile(db: Session, bank_id: str, actor_id: str, user_id: str) -> dict:
    user = _user_or_404(db, bank_id, user_id)
    _audit(db, bank_id, actor_id, "customer_profile_viewed", "user", user_id)
    profile = _user_summary(db, user)
    report = get_score_report(db, user.id)
    consent = db.query(UserConsent).filter(UserConsent.user_id == user.id, UserConsent.consent_type == "score_processing").one_or_none()
    contributions = db.query(Contribution).filter(Contribution.user_id == user.id).all()
    full_contributions = sum(1 for contribution in contributions if contribution.status == "full")
    profile.update({
        "score_report": report,
        "context": user.context,
        "score_computed_at": report.get("computed_at"),
        "score_processing_consent": bool(consent and consent.granted),
        "contribution_count": len(contributions),
        "on_time_contribution_rate": round(full_contributions / len(contributions), 2) if contributions else None,
        "float_eligibility": "eligible" if report["score"] > 120 else "locked",
        "float_eligibility_reason": "Float is not part of this MVP." if report["score"] > 120 else "Complete a Sura Lock before Float can unlock.",
    })
    return profile


def get_user_score(db: Session, bank_id: str, actor_id: str, user_id: str) -> dict:
    _user_or_404(db, bank_id, user_id)
    _audit(db, bank_id, actor_id, "customer_score_viewed", "user", user_id)
    report = public_score_report(db, user_id)
    history = db.query(ScoreHistory).filter(ScoreHistory.user_id == user_id).order_by(ScoreHistory.computed_at.desc(), ScoreHistory.id.desc()).all()
    return {
        "user_id": user_id,
        "current": report,
        "history": [
            {
                **serialize_score_history_entry(row),
                "computed_at": row.computed_at.isoformat() if row.computed_at else None,
            }
            for row in history
        ],
    }


def get_user_commitments(db: Session, bank_id: str, user_id: str) -> list[dict]:
    _user_or_404(db, bank_id, user_id)
    rows = db.query(Commitment).join(CommitmentMember).filter(CommitmentMember.user_id == user_id).order_by(Commitment.created_at.desc()).all()
    result = []
    for row in rows:
        membership = db.query(CommitmentMember).filter(CommitmentMember.commitment_id == row.id, CommitmentMember.user_id == user_id).one()
        beneficiary = db.query(CommitmentBeneficiary).filter(CommitmentBeneficiary.commitment_id == row.id, CommitmentBeneficiary.user_id == user_id).order_by(CommitmentBeneficiary.cycle_number.desc()).first()
        paid = db.query(func.coalesce(func.sum(Contribution.amount), 0)).filter(Contribution.commitment_id == row.id, Contribution.user_id == user_id).scalar()
        voucher = db.query(Voucher).filter(Voucher.commitment_id == row.id, Voucher.beneficiary_id == user_id).order_by(Voucher.cycle_number.desc()).first()
        result.append({
            "commitment_id": row.id, "title": row.title, "status": row.status, "type": row.type,
            "vendor_id": row.vendor_id, "contribution_amount": row.contribution_amount, "cycles": row.cycles,
            "completed_cycle_count": row.completed_cycle_count, "member_role": membership.role,
            "payout_cycle": beneficiary.cycle_number if beneficiary else None, "payout_status": beneficiary.status if beneficiary else None,
            "contributed_amount": int(paid or 0), "voucher_status": voucher.status if voucher else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })
    return result


def get_customer_commitment_detail(
    db: Session,
    bank_id: str,
    actor_id: str,
    user_id: str,
    commitment_id: str,
) -> dict:
    """Return evidence for one commitment the scoped customer actually joined."""
    _user_or_404(db, bank_id, user_id)
    membership = (
        db.query(CommitmentMember)
        .filter(
            CommitmentMember.user_id == user_id,
            CommitmentMember.commitment_id == commitment_id,
        )
        .one_or_none()
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Commitment not found for this customer.")
    _audit(db, bank_id, actor_id, "customer_commitment_viewed", "commitment", commitment_id, {"user_id": user_id})
    return get_commitment(db, bank_id, commitment_id)


def get_user_activity(db: Session, bank_id: str, user_id: str) -> list[dict]:
    _user_or_404(db, bank_id, user_id)
    score_events = db.query(ScoreHistory).filter(ScoreHistory.user_id == user_id).all()
    commitment_events = db.query(CommitmentActivity).join(CommitmentMember, CommitmentMember.commitment_id == CommitmentActivity.commitment_id).filter(CommitmentMember.user_id == user_id).all()
    consent_events = db.query(UserConsent).filter(UserConsent.user_id == user_id).all()
    flag_events = db.query(RiskFlag).filter(RiskFlag.bank_id == bank_id, RiskFlag.user_id == user_id).all()
    events = [{"type": "score_updated", "id": row.id, "reason": row.reason, "occurred_at": row.computed_at} for row in score_events]
    events.extend({"type": row.event_type, "id": row.id, "details": json.loads(row.detail_json), "occurred_at": row.occurred_at} for row in commitment_events)
    events.extend({"type": "consent_updated", "id": row.id, "details": {"consent_type": row.consent_type, "granted": row.granted}, "occurred_at": row.recorded_at} for row in consent_events)
    events.extend({"type": "risk_flag", "id": row.id, "details": {"rule": row.rule, "status": row.status, "severity": row.severity}, "occurred_at": row.created_at} for row in flag_events)
    return [{**row, "occurred_at": row["occurred_at"].isoformat() if row["occurred_at"] else None} for row in sorted(events, key=lambda item: item["occurred_at"] or datetime.min, reverse=True)]


def list_commitments(db: Session, bank_id: str, *, query: str | None = None, status_filter: str | None = None, vendor_id: str | None = None, member_id: str | None = None) -> list[dict]:
    rows = db.query(Commitment).join(CommitmentMember).join(User, User.id == CommitmentMember.user_id).filter(User.bank_id == bank_id)
    if query:
        token = f"%{query.strip()}%"
        rows = rows.filter(or_(Commitment.id.ilike(token), Commitment.title.ilike(token), Commitment.vendor_id.ilike(token), CommitmentMember.user_id.ilike(token)))
    if status_filter:
        rows = rows.filter(Commitment.status == status_filter)
    if vendor_id:
        rows = rows.filter(Commitment.vendor_id == vendor_id)
    if member_id:
        rows = rows.filter(CommitmentMember.user_id == member_id)
    rows = rows.distinct().order_by(Commitment.created_at.desc()).all()
    lifecycle_changed = any(refresh_commitment_lifecycle(db, row) for row in rows)
    if lifecycle_changed:
        db.commit()
    result = []
    for row in rows:
        members = db.query(CommitmentMember).filter(CommitmentMember.commitment_id == row.id).count()
        contributed = db.query(func.coalesce(func.sum(Contribution.amount), 0)).filter(Contribution.commitment_id == row.id).scalar()
        result.append({"commitment_id": row.id, "title": row.title, "status": row.status, "type": row.type, "vendor_id": row.vendor_id, "member_count": members, "cycles": row.cycles, "current_cycle_number": row.current_cycle_number, "completed_cycle_count": row.completed_cycle_count, "current_cycle_due_at": row.current_cycle_due_at.isoformat() if row.current_cycle_due_at else None, "grace_period_hours": row.grace_period_hours, "missed_cycle_policy": row.missed_cycle_policy, "missed_cycle_count": row.missed_cycle_count, "total_contributed": int(contributed or 0), "created_at": row.created_at.isoformat() if row.created_at else None})
    return result


def assert_commitment_in_bank(db: Session, bank_id: str, commitment_id: str) -> Commitment:
    """Confirm a commitment belongs to this bank, without reading or changing it.

    Read-only endpoints use this rather than get_commitment so that asking a
    question about a Lock cannot advance its deadline state as a side effect.
    """
    if not db.query(CommitmentMember).join(User, User.id == CommitmentMember.user_id).filter(CommitmentMember.commitment_id == commitment_id, User.bank_id == bank_id).first():
        raise HTTPException(status_code=404, detail="Commitment not found for this bank.")
    row = db.get(Commitment, commitment_id)
    # The membership check above passed, so a missing commitment row means the
    # member rows outlived their commitment. Reading row.id unguarded here would
    # raise AttributeError and return a 500 instead of the 404 the caller expects.
    if row is None:
        raise HTTPException(status_code=404, detail="Commitment not found for this bank.")
    return row


def get_commitment(db: Session, bank_id: str, commitment_id: str) -> dict:
    row = assert_commitment_in_bank(db, bank_id, commitment_id)
    if refresh_commitment_lifecycle(db, row):
        db.commit()
    vendor = db.get(Vendor, row.vendor_id)
    members = db.query(CommitmentMember).join(User, User.id == CommitmentMember.user_id).filter(CommitmentMember.commitment_id == row.id, User.bank_id == bank_id).all()
    member_users = {user.id: user for user in db.query(User).filter(User.id.in_([member.user_id for member in members])).all()} if members else {}
    contributions = db.query(Contribution).join(User, User.id == Contribution.user_id).filter(Contribution.commitment_id == row.id, User.bank_id == bank_id).order_by(Contribution.cycle_number, Contribution.paid_at).all()
    beneficiaries = db.query(CommitmentBeneficiary).join(User, User.id == CommitmentBeneficiary.user_id).filter(CommitmentBeneficiary.commitment_id == row.id, User.bank_id == bank_id).order_by(CommitmentBeneficiary.cycle_number).all()
    vouchers = db.query(Voucher).join(User, User.id == Voucher.beneficiary_id).filter(Voucher.commitment_id == row.id, User.bank_id == bank_id).all()
    voucher_by_cycle = {voucher.cycle_number: voucher for voucher in vouchers}
    redemptions = db.query(Redemption).join(User, User.id == Redemption.beneficiary_id).filter(Redemption.commitment_id == row.id, User.bank_id == bank_id).all()
    redemption_by_cycle = {redemption.cycle_number: redemption for redemption in redemptions}
    activity = db.query(CommitmentActivity).filter(CommitmentActivity.commitment_id == row.id).order_by(CommitmentActivity.occurred_at.desc()).all()
    cases = db.query(CommitmentCase).filter(CommitmentCase.commitment_id == row.id, CommitmentCase.bank_id == bank_id).order_by(CommitmentCase.opened_at.desc()).all()
    member_views = []
    for member in members:
        score = get_score_report(db, member.user_id)
        member_views.append({
            "user_id": member.user_id,
            "name": member_users[member.user_id].name,
            "role": member.role,
            "score": score["score"],
            "tier": score["tier"],
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        })
    return {
        "commitment_id": row.id, "title": row.title, "status": row.status, "type": row.type,
        "vendor": {"vendor_id": row.vendor_id, "name": vendor.name if vendor else None, "verified": bool(vendor and vendor.verified_at)},
        "product": (
            {"product_id": row.vendor_product_id, "name": row.product_name_snapshot, "price": row.product_price_snapshot}
            if row.vendor_product_id is not None
            else None
        ),
        "contribution_amount": row.contribution_amount, "frequency": row.frequency, "cycles": row.cycles,
        "current_cycle_number": row.current_cycle_number, "completed_cycle_count": row.completed_cycle_count,
        "first_cycle_due_at": row.first_cycle_due_at.isoformat() if row.first_cycle_due_at else None,
        "current_cycle_due_at": row.current_cycle_due_at.isoformat() if row.current_cycle_due_at else None,
        "grace_period_hours": row.grace_period_hours, "missed_cycle_policy": row.missed_cycle_policy, "missed_cycle_count": row.missed_cycle_count,
        "payout_order": json.loads(row.payout_order_json),
        "members": member_views,
        "contributions": [{"contribution_id": contribution.id, "user_id": contribution.user_id, "cycle_number": contribution.cycle_number, "amount": contribution.amount, "status": contribution.status, "paid_at": contribution.paid_at.isoformat() if contribution.paid_at else None} for contribution in contributions],
        "payout_schedule": [{"cycle_number": beneficiary.cycle_number, "beneficiary_id": beneficiary.user_id, "amount": beneficiary.payout_amount, "status": beneficiary.status, "voucher_status": voucher_by_cycle[beneficiary.cycle_number].status if beneficiary.cycle_number in voucher_by_cycle else None, "settlement_status": redemption_by_cycle[beneficiary.cycle_number].status if beneficiary.cycle_number in redemption_by_cycle else None} for beneficiary in beneficiaries],
        "activity": [{"activity_id": item.id, "type": item.event_type, "actor_user_id": item.actor_user_id, "cycle_number": item.cycle_number, "details": json.loads(item.detail_json), "occurred_at": item.occurred_at.isoformat() if item.occurred_at else None} for item in activity],
        "support_cases": [{"case_id": case.id, "status": case.status, "reason": case.reason, "resolution_note": case.resolution_note, "opened_at": case.opened_at.isoformat() if case.opened_at else None, "resolved_at": case.resolved_at.isoformat() if case.resolved_at else None} for case in cases],
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def overview(db: Session, bank_id: str, *, date_from: datetime | None = None, date_to: datetime | None = None) -> dict:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from must be before date_to.")
    commitments = list_commitments(db, bank_id)
    bank = db.get(BankPartner, bank_id)
    if bank is None:
        raise HTTPException(status_code=404, detail="Bank not found.")
    customer_count = (
        db.query(User)
        .outerjoin(BankStaff, BankStaff.user_id == User.id)
        .filter(User.bank_id == bank_id, BankStaff.id.is_(None))
        .count()
    )
    portfolio_balance_snapshot = (
        db.query(func.coalesce(func.sum(User.available_balance), 0))
        .outerjoin(BankStaff, BankStaff.user_id == User.id)
        .filter(User.bank_id == bank_id, BankStaff.id.is_(None))
        .scalar()
    )
    contributions = db.query(Contribution).join(User, User.id == Contribution.user_id).filter(User.bank_id == bank_id)
    if date_from:
        contributions = contributions.filter(Contribution.paid_at >= date_from)
    if date_to:
        contributions = contributions.filter(Contribution.paid_at <= date_to)
    contribution_total = contributions.with_entities(func.coalesce(func.sum(Contribution.amount), 0)).scalar()
    settlements_query = db.query(Redemption).join(User, User.id == Redemption.beneficiary_id).filter(User.bank_id == bank_id)
    if date_from:
        settlements_query = settlements_query.filter(Redemption.redeemed_at >= date_from)
    if date_to:
        settlements_query = settlements_query.filter(Redemption.redeemed_at <= date_to)
    recent_settlements = settlements_query.order_by(Redemption.redeemed_at.desc()).limit(5).all()
    recent_audit = db.query(BankAuditEvent).filter(BankAuditEvent.bank_id == bank_id).order_by(BankAuditEvent.occurred_at.desc()).limit(5).all()
    return {
        "bank_id": bank.id,
        "bank_name": bank.name,
        "environment": bank.environment,
        "customers": customer_count,
        # Bank-owned, simulated customer-balance data. This is neither a
        # Sura-held balance nor a settlement total.
        "portfolio_available_balance_snapshot": int(portfolio_balance_snapshot or 0),
        "portfolio_balance_currency": "NGN",
        "active_commitments": sum(1 for row in commitments if row["status"] == "active"),
        "total_contributed": int(contribution_total or 0),
        "completion_rate": round(sum(1 for row in commitments if row["status"] == "completed") / len(commitments), 2) if commitments else 0,
        "open_flags": db.query(RiskFlag).filter(RiskFlag.bank_id == bank_id, RiskFlag.status == "open").count(),
        "pending_settlements": 0,
        "recent_settlements": [{"settlement_id": row.id, "commitment_id": row.commitment_id, "status": row.status, "amount": row.amount, "redeemed_at": row.redeemed_at.isoformat() if row.redeemed_at else None, "simulated": True} for row in recent_settlements],
        "recent_activity": [{"event_id": row.id, "event_type": row.event_type, "subject_id": row.subject_id, "occurred_at": row.occurred_at.isoformat() if row.occurred_at else None} for row in recent_audit],
    }


def audit_log(db: Session, bank_id: str, *, user_id: str | None = None, commitment_id: str | None = None, event_type: str | None = None, actor_id: str | None = None, date_from: datetime | None = None, date_to: datetime | None = None) -> list[dict]:
    scores = db.query(ScoreHistory).filter(ScoreHistory.bank_id == bank_id).all()
    access = db.query(BankAuditEvent).filter(BankAuditEvent.bank_id == bank_id).all()
    events = [{"type": "score", "id": row.id, "user_id": row.user_id, "event_type": row.event_type, "reason": row.reason, "occurred_at": row.computed_at} for row in scores]
    events.extend({"type": "bank_access", "id": row.id, "actor_id": row.actor_id, "event_type": row.event_type, "subject_id": row.subject_id, "occurred_at": row.occurred_at} for row in access)
    if user_id:
        events = [event for event in events if event.get("user_id") == user_id or event.get("subject_id") == user_id]
    if commitment_id:
        events = [event for event in events if event.get("subject_id") == commitment_id]
    if event_type:
        events = [event for event in events if event.get("event_type") == event_type]
    if actor_id:
        events = [event for event in events if event.get("actor_id") == actor_id]
    if date_from:
        events = [event for event in events if event["occurred_at"] and event["occurred_at"] >= date_from]
    if date_to:
        events = [event for event in events if event["occurred_at"] and event["occurred_at"] <= date_to]
    return [{**event, "occurred_at": event["occurred_at"].isoformat() if event["occurred_at"] else None} for event in sorted(events, key=lambda item: item["occurred_at"] or datetime.min, reverse=True)]


def export_audit_log(db: Session, bank_id: str, actor_id: str) -> str:
    rows = audit_log(db, bank_id)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "type", "event_type", "user_id", "subject_id", "actor_id", "reason", "occurred_at"], extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    _audit(db, bank_id, actor_id, "audit_log_exported", "audit_log", bank_id, {"row_count": len(rows)})
    db.commit()
    return output.getvalue()


def list_flags(db: Session, bank_id: str, user_id: str | None = None, *, status_filter: str | None = None, severity: str | None = None, rule: str | None = None) -> list[dict]:
    rows = db.query(RiskFlag).filter(RiskFlag.bank_id == bank_id)
    if user_id:
        rows = rows.filter(RiskFlag.user_id == user_id)
    if status_filter:
        rows = rows.filter(RiskFlag.status == status_filter)
    if severity:
        rows = rows.filter(RiskFlag.severity == severity)
    if rule:
        rows = rows.filter(RiskFlag.rule == rule)
    return [_serialize_flag(row) for row in rows.order_by(RiskFlag.created_at.desc()).all()]


def get_flag(db: Session, bank_id: str, flag_id: str) -> dict:
    row = db.query(RiskFlag).filter(RiskFlag.id == flag_id, RiskFlag.bank_id == bank_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Risk flag not found.")
    history = db.query(BankAuditEvent).filter(BankAuditEvent.bank_id == bank_id, BankAuditEvent.subject_type == "risk_flag", BankAuditEvent.subject_id == flag_id).order_by(BankAuditEvent.occurred_at.desc()).all()
    return {**_serialize_flag(row), "review_history": [{"event_type": event.event_type, "actor_id": event.actor_id, "details": json.loads(event.detail_json), "occurred_at": event.occurred_at.isoformat() if event.occurred_at else None} for event in history]}


def revoke_member_sessions(db: Session, bank_id: str, actor_id: str, user_id: str) -> dict:
    """End every live session for one of this bank's members.

    The only reliable way to sign a member out everywhere is to raise the
    generation on their account, because the platform deliberately does not
    store live tokens: it is not a session store. Every session this service
    issued then fails the re-check on its next request, and any session still
    outstanding stops working without waiting for its expiry.
    """
    member = _user_or_404(db, bank_id, user_id)
    member.session_invalidated_at = datetime.utcnow()
    _audit(db, bank_id, actor_id, "member_sessions_revoked", "user", user_id, {})
    audit.record(
        db,
        event_type=audit.SESSION_REVOKED_BY_STAFF,
        subject_type="user",
        subject_id=user_id,
        actor_id=actor_id,
        institution_id=bank_id,
        detail={"scope": "all_sessions"},
    )
    db.commit()
    return {"user_id": member.id, "sessions_revoked": True, "at": datetime.utcnow().isoformat()}


def _serialize_flag(row: RiskFlag) -> dict:
    # resolved_by is returned because a reviewer who cannot see who decided a
    # flag cannot audit the queue they are working through.
    return {"flag_id": row.id, "user_id": row.user_id, "rule": row.rule, "severity": row.severity, "status": row.status, "evidence": json.loads(row.evidence_json), "resolution_note": row.resolution_note, "resolved_by": row.resolved_by, "created_at": row.created_at.isoformat() if row.created_at else None, "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None}


def resolve_flag(db: Session, bank_id: str, actor_id: str, flag_id: str, action: str, note: str) -> dict:
    if action not in {"dismissed", "confirmed", "escalated"}:
        raise HTTPException(status_code=400, detail="Flag action must be dismissed, confirmed, or escalated.")
    row = db.query(RiskFlag).filter(RiskFlag.id == flag_id, RiskFlag.bank_id == bank_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Risk flag not found.")
    if row.status != "open":
        # Re-resolving an already-decided flag would overwrite who decided it,
        # destroying the only record of the original call.
        raise HTTPException(status_code=409, detail=f"This flag is already {row.status}.")
    row.status, row.resolution_note, row.resolved_by, row.resolved_at = action, note, actor_id, datetime.utcnow()
    _audit(db, bank_id, actor_id, "risk_flag_resolved", "risk_flag", flag_id, {"action": action})
    db.commit()
    return _serialize_flag(row)


def run_risk_rules(db: Session, bank_id: str, actor_id: str, user_ids: list[str] | None = None) -> dict:
    """Evaluate the rule set for this bank and open a flag for each new finding.

    The engine only ever opens flags. Restricting an account stays a separate,
    explicit, human decision through ``apply_restriction``.
    """
    result = risk_rules.run_rules(db, bank_id, user_ids)
    _audit(db, bank_id, actor_id, "risk_rules_evaluated", "bank", bank_id, {"members_evaluated": result["members_evaluated"], "flags_created_count": result["flags_created_count"]})
    db.commit()
    return result


def settlements(db: Session, bank_id: str, *, query: str | None = None, status_filter: str | None = None, vendor_id: str | None = None, user_id: str | None = None, commitment_id: str | None = None) -> list[dict]:
    rows = db.query(Redemption).join(User, User.id == Redemption.beneficiary_id).filter(User.bank_id == bank_id)
    if query:
        token = f"%{query.strip()}%"
        rows = rows.filter(or_(Redemption.id.ilike(token), Redemption.voucher_code.ilike(token), Redemption.vendor_id.ilike(token), Redemption.commitment_id.ilike(token), Redemption.beneficiary_id.ilike(token)))
    if status_filter:
        rows = rows.filter(Redemption.status == status_filter)
    if vendor_id:
        rows = rows.filter(Redemption.vendor_id == vendor_id)
    if user_id:
        rows = rows.filter(Redemption.beneficiary_id == user_id)
    if commitment_id:
        rows = rows.filter(Redemption.commitment_id == commitment_id)
    rows = rows.order_by(Redemption.redeemed_at.desc()).all()
    return [{"settlement_id": row.id, "commitment_id": row.commitment_id, "vendor_id": row.vendor_id, "amount": row.amount, "voucher_code": row.voucher_code, "status": row.status, "redeemed_at": row.redeemed_at.isoformat() if row.redeemed_at else None, "simulated": True} for row in rows]
