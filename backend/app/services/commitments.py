import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.bank import risk_rules
from app.bank.models import BankStaff
from app.models import (
    Commitment,
    CommitmentActivity,
    CommitmentBeneficiary,
    CommitmentCase,
    CommitmentMember,
    Contribution,
    Redemption,
    ScoreHistory,
    User,
    UserConsent,
    Vendor,
    Voucher,
)
from app.schemas import ContributionRequest, LockRequest
from app.services.contribution_engine import dump_rule_trace, evaluate_contribution
from app.services.lock_lifecycle import SUPPORTED_FREQUENCIES, advance_due_at, deadline_state, default_first_due_at
from app.services.payout_rules import apply_anchor_and_cap_rule, build_payout_schedule
from app.services.score_service import public_score_report, record_score_snapshot, refresh_commitment_member_scores
from app.services.scoring import ENTRY_TIER_BASELINE
from core.config import get_settings

ENTRY_TIER_SCORE = ENTRY_TIER_BASELINE


def _normalize_due_at(value: datetime | None) -> datetime | None:
    """Persist all Lock schedule times as naive UTC, matching existing models."""
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _record_activity(
    db: Session,
    commitment_id: str,
    event_type: str,
    *,
    actor_user_id: str | None = None,
    cycle_number: int | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    db.add(
        CommitmentActivity(
            id=str(uuid.uuid4()),
            commitment_id=commitment_id,
            event_type=event_type,
            actor_user_id=actor_user_id,
            cycle_number=cycle_number,
            detail_json=json.dumps(details or {}),
            occurred_at=datetime.utcnow(),
        )
    )


def _serialize_voucher(voucher: Voucher) -> dict[str, Any]:
    return {
        "voucher_id": voucher.id,
        "commitment_id": voucher.commitment_id,
        "beneficiary_id": voucher.beneficiary_id,
        "vendor_id": voucher.vendor_id,
        "cycle_number": voucher.cycle_number,
        "amount": voucher.amount,
        "voucher_code": voucher.code,
        "status": voucher.status,
        "issued_at": voucher.issued_at.isoformat() if voucher.issued_at else None,
        "redeemed_at": voucher.redeemed_at.isoformat() if voucher.redeemed_at else None,
    }


def _serialize_voucher_state(voucher: Voucher) -> dict[str, Any]:
    return {
        "voucher_id": voucher.id,
        "commitment_id": voucher.commitment_id,
        "beneficiary_id": voucher.beneficiary_id,
        "vendor_id": voucher.vendor_id,
        "cycle_number": voucher.cycle_number,
        "amount": voucher.amount,
        "status": voucher.status,
        "issued_at": voucher.issued_at.isoformat() if voucher.issued_at else None,
        "redeemed_at": voucher.redeemed_at.isoformat() if voucher.redeemed_at else None,
    }


def _first_name(user: User | None) -> str | None:
    """Return the smallest member-display field the PWA needs."""
    return user.name.split(maxsplit=1)[0] if user is not None and user.name else None


def _issue_voucher_if_needed(
    db: Session,
    commitment: Commitment,
    beneficiary: CommitmentBeneficiary,
) -> Voucher:
    voucher = (
        db.query(Voucher)
        .filter(Voucher.commitment_id == commitment.id, Voucher.cycle_number == beneficiary.cycle_number)
        .one_or_none()
    )
    if voucher is not None:
        return voucher
    voucher = Voucher(
        id=str(uuid.uuid4()),
        commitment_id=commitment.id,
        beneficiary_id=beneficiary.user_id,
        vendor_id=commitment.vendor_id,
        cycle_number=beneficiary.cycle_number,
        amount=beneficiary.payout_amount,
        code=f"SURA-{uuid.uuid4().hex[:10].upper()}",
        status="ready",
        issued_at=datetime.utcnow(),
    )
    db.add(voucher)
    _record_activity(
        db,
        commitment.id,
        "voucher_issued",
        cycle_number=beneficiary.cycle_number,
        details={"beneficiary_id": beneficiary.user_id, "vendor_id": commitment.vendor_id, "amount": beneficiary.payout_amount},
    )
    return voucher


def _require_member(db: Session, commitment_id: str, user_id: str) -> CommitmentMember:
    member = (
        db.query(CommitmentMember)
        .filter(CommitmentMember.commitment_id == commitment_id, CommitmentMember.user_id == user_id)
        .one_or_none()
    )
    if member is None:
        raise HTTPException(status_code=403, detail="You are not a member of this commitment.")
    if member.role == "replaced":
        raise HTTPException(status_code=403, detail="You were replaced before this commitment became active.")
    return member


def _activate_if_fully_joined(db: Session, commitment: Commitment) -> None:
    db.flush()
    invited_count = (
        db.query(CommitmentMember)
        .filter(CommitmentMember.commitment_id == commitment.id, CommitmentMember.role == "invited")
        .count()
    )
    declined_count = (
        db.query(CommitmentMember)
        .filter(CommitmentMember.commitment_id == commitment.id, CommitmentMember.role == "declined")
        .count()
    )
    if invited_count == 0 and declined_count == 0 and commitment.status == "pending_members":
        commitment.status = "active"
        commitment.current_cycle_due_at = commitment.first_cycle_due_at


def _refresh_lifecycle(db: Session, commitment: Commitment, *, now: datetime | None = None) -> bool:
    """Persist deadline-driven state transitions for the current unpaid cycle."""
    if commitment.status in {"pending_members", "cancelled", "completed", "under_review", "missed"}:
        return False
    now = now or datetime.utcnow()
    # Most list/home reads happen before the deadline. The calculated state is
    # already identical in that case, so looking up a beneficiary cannot change
    # anything and only adds one query per active Lock.
    next_state = deadline_state(
        due_at=commitment.current_cycle_due_at,
        grace_period_hours=commitment.grace_period_hours,
        now=now,
    )
    if next_state == commitment.status:
        return False
    beneficiary = (
        db.query(CommitmentBeneficiary)
        .filter(
            CommitmentBeneficiary.commitment_id == commitment.id,
            CommitmentBeneficiary.cycle_number == commitment.current_cycle_number,
        )
        .one_or_none()
    )
    if beneficiary is None or beneficiary.status in {"paid", "redeemed"}:
        return False
    previous = commitment.status
    commitment.status = next_state
    beneficiary.status = next_state if next_state in {"overdue", "missed"} else "scheduled"
    if next_state == "missed" and previous != "missed":
        commitment.missed_cycle_count += 1
    _record_activity(
        db,
        commitment.id,
        f"cycle_{next_state}",
        cycle_number=commitment.current_cycle_number,
        details={
            "due_at": commitment.current_cycle_due_at.isoformat() if commitment.current_cycle_due_at else None,
            "grace_period_hours": commitment.grace_period_hours,
            "previous_status": previous,
            "missed_cycle_policy": commitment.missed_cycle_policy,
        },
    )
    if next_state == "missed":
        # A missed cycle is a persisted Lock outcome, so it must receive the
        # same explainable Score treatment as a paid/recovered cycle. This is
        # deliberately triggered by the lifecycle transition, not guessed by
        # the PWA from elapsed time.
        _refresh_score_history_for_commitment(
            db,
            commitment.id,
            event_id=f"{commitment.id}:cycle:{commitment.current_cycle_number}:missed",
            event_type="cycle_missed",
            reason="cycle_missed",
        )
        if commitment.missed_cycle_policy == "cancel_and_refund":
            # Sura does not custody funds. In the demo this is a durable,
            # auditable refund instruction for the bank rail simulator; a
            # production adapter will execute and reconcile the transfer.
            paid_total = (
                db.query(func.coalesce(func.sum(Contribution.amount), 0))
                .filter(
                    Contribution.commitment_id == commitment.id,
                    Contribution.cycle_number == commitment.current_cycle_number,
                )
                .scalar()
            )
            commitment.status = "cancelled"
            beneficiary.status = "cancelled"
            _record_activity(
                db,
                commitment.id,
                "refund_instruction_created",
                cycle_number=commitment.current_cycle_number,
                details={
                    "policy": "cancel_and_refund",
                    "simulated_refund_total": int(paid_total or 0),
                    "settlement": "bank_rail_required",
                },
            )
    return True


def refresh_commitment_lifecycle(db: Session, commitment: Commitment, *, now: datetime | None = None) -> bool:
    """Refresh a Lock's deadline state for read models outside this module.

    The Bank Portal is a consumer of the same Lock record, not a second
    lifecycle engine. Keeping this small public boundary prevents the portal
    from duplicating deadline rules or showing stale evidence when no member
    request happens first.
    """
    return _refresh_lifecycle(db, commitment, now=now)


def _normalize_member_ids(member_ids: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for member_id in member_ids:
        if member_id in seen:
            raise HTTPException(status_code=400, detail="Member IDs must be unique.")
        seen.add(member_id)
        normalized.append(member_id)
    return normalized


def _require_rotating_group_size(member_ids: list[str]) -> None:
    """A rotating pool cannot have fewer than two final members."""
    if len(member_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail="A rotating commitment requires at least two distinct members.",
        )


def _ensure_member_user(db: Session, user_id: str) -> None:
    user = db.get(User, user_id)
    if user is not None:
        is_bank_staff = db.query(BankStaff.id).filter(BankStaff.user_id == user_id).first() is not None
        if user.role != "individual" or is_bank_staff:
            raise HTTPException(status_code=400, detail="Commitment members must be individual Sura accounts.")
        return

    if get_settings().is_production:
        raise HTTPException(status_code=400, detail="Every commitment member must have a Sura account.")

    db.add(
        User(
            id=user_id,
            name=user_id,
            phone=f"demo-{user_id}@sura.local",
        )
    )


def _require_score_processing_consent(db: Session, user_id: str) -> None:
    consent = (
        db.query(UserConsent)
        .filter(UserConsent.user_id == user_id, UserConsent.consent_type == "score_processing")
        .one_or_none()
    )
    if consent is None or not consent.granted:
        raise HTTPException(
            status_code=400,
            detail="Score-processing consent is required before creating or joining a commitment.",
        )


def _latest_score_by_user(db: Session, member_ids: list[str]) -> dict[str, int]:
    if not member_ids:
        return {}

    rows = (
        db.query(ScoreHistory.user_id, ScoreHistory.score)
        .filter(ScoreHistory.user_id.in_(member_ids))
        .order_by(ScoreHistory.user_id, ScoreHistory.computed_at.desc(), ScoreHistory.id.desc())
        .all()
    )

    scores: dict[str, int] = {}
    for user_id, score in rows:
        if user_id not in scores:
            scores[user_id] = score
    return scores


def _build_payout_order(
    db: Session, member_ids: list[str], requested_order: list[str] | None
) -> tuple[list[str], bool]:
    if requested_order is not None and requested_order != member_ids:
        raise HTTPException(
            status_code=400,
            detail="payout_order must match members in the same order.",
        )
    scores = _latest_score_by_user(db, member_ids)
    if not scores:
        if requested_order is None:
            raise HTTPException(
                status_code=400,
                detail="Genesis commitments require a payout_order chosen by the group.",
            )
        return requested_order, True

    ranked = sorted(
        enumerate(member_ids),
        key=lambda item: (-scores.get(item[1], ENTRY_TIER_SCORE), item[0]),
    )
    return [member_id for _, member_id in ranked], False


def preview_lock(
    db: Session, payload: LockRequest, authenticated_creator_id: str
) -> dict[str, Any]:
    """Return the deterministic Lock plan without storing a commitment."""
    payload.first_cycle_due_at = _normalize_due_at(payload.first_cycle_due_at)
    if payload.type != "rotating":
        raise HTTPException(status_code=400, detail="Only rotating commitments are supported.")
    if not payload.members:
        raise HTTPException(status_code=400, detail="At least one member is required.")
    if payload.contribution_amount <= 0:
        raise HTTPException(status_code=400, detail="Contribution amount must be positive.")
    if payload.cycles <= 0:
        raise HTTPException(status_code=400, detail="Cycles must be positive.")
    if payload.contribution_frequency not in SUPPORTED_FREQUENCIES:
        raise HTTPException(status_code=400, detail="Contribution frequency must be daily, weekly, or monthly.")
    if payload.first_cycle_due_at is not None and payload.first_cycle_due_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="first_cycle_due_at must be in the future.")

    member_ids = _normalize_member_ids(payload.members)
    if payload.creator_id and payload.creator_id != authenticated_creator_id:
        raise HTTPException(status_code=403, detail="creator_id must match the authenticated user.")
    if authenticated_creator_id not in member_ids:
        member_ids = _normalize_member_ids([authenticated_creator_id, *member_ids])
    _require_rotating_group_size(member_ids)
    if payload.cycles != len(member_ids):
        raise HTTPException(status_code=400, detail="A rotating commitment must have one cycle per member.")

    vendor = db.get(Vendor, payload.vendor_id)
    if vendor is None or vendor.verified_at is None:
        raise HTTPException(status_code=400, detail="Commitment vendor must be verified before it can be selected.")
    members = [db.get(User, member_id) for member_id in member_ids]
    if any(member is None for member in members):
        raise HTTPException(status_code=400, detail="Every commitment member must have a Sura account.")
    member_ids_with_bank_staff = {
        row.user_id for row in db.query(BankStaff.user_id).filter(BankStaff.user_id.in_(member_ids)).all()
    }
    if any(member.role != "individual" for member in members if member is not None) or member_ids_with_bank_staff:
        raise HTTPException(status_code=400, detail="Commitment members must be individual Sura accounts.")

    payout_order, genesis_group = _build_payout_order(db, member_ids, payload.payout_order)
    payout_schedule = build_payout_schedule(payout_order, payload.contribution_amount, payload.cycles)
    first_payout_is_within_cap = not payout_schedule or (
        apply_anchor_and_cap_rule(payout_schedule[0]["amount"], 1) == payout_schedule[0]["amount"]
    )
    return {
        "members": member_ids,
        "payout_order": payout_order,
        "payout_schedule": payout_schedule,
        "genesis_group": genesis_group,
        "first_payout_is_within_cap": first_payout_is_within_cap,
        "can_create": first_payout_is_within_cap,
        "blocking_reason": (
            None
            if first_payout_is_within_cap
            else "Genesis commitments must keep the first pooled payout within the configured cap."
        ),
    }


def _serialize_commitment(commitment: Commitment, db: Session) -> dict[str, Any]:
    """Serialize one Lock through the same batch path used by list reads."""
    return _serialize_commitments([commitment], db)[0]


def _serialize_commitments(commitments: list[Commitment], db: Session) -> list[dict[str, Any]]:
    """Serialize Locks without multiplying database round trips per Lock.

    The member home and commitment-list APIs return complete Lock evidence. The
    earlier implementation fetched members, beneficiaries, contributions,
    vouchers, member users, and a vendor separately for every Lock. This helper
    loads each relation once for the whole page, then feeds the unchanged
    serializer. It keeps the API shape stable while making request cost grow
    with relation types rather than commitment count.
    """
    if not commitments:
        return []

    commitment_ids = [commitment.id for commitment in commitments]
    members_by_commitment: dict[str, list[CommitmentMember]] = defaultdict(list)
    for row in (
        db.query(CommitmentMember)
        .filter(CommitmentMember.commitment_id.in_(commitment_ids))
        .order_by(
            CommitmentMember.commitment_id.asc(),
            CommitmentMember.joined_at.asc(),
            CommitmentMember.user_id.asc(),
        )
        .all()
    ):
        members_by_commitment[row.commitment_id].append(row)

    beneficiaries_by_commitment: dict[str, list[CommitmentBeneficiary]] = defaultdict(list)
    for row in (
        db.query(CommitmentBeneficiary)
        .filter(CommitmentBeneficiary.commitment_id.in_(commitment_ids))
        .order_by(CommitmentBeneficiary.commitment_id.asc(), CommitmentBeneficiary.cycle_number.asc())
        .all()
    ):
        beneficiaries_by_commitment[row.commitment_id].append(row)

    contributions_by_commitment: dict[str, list[Contribution]] = defaultdict(list)
    for row in (
        db.query(Contribution)
        .filter(Contribution.commitment_id.in_(commitment_ids))
        .order_by(
            Contribution.commitment_id.asc(),
            Contribution.cycle_number.asc(),
            Contribution.paid_at.asc(),
            Contribution.user_id.asc(),
        )
        .all()
    ):
        contributions_by_commitment[row.commitment_id].append(row)

    vouchers_by_commitment: dict[str, list[Voucher]] = defaultdict(list)
    for row in (
        db.query(Voucher)
        .filter(Voucher.commitment_id.in_(commitment_ids))
        .order_by(Voucher.commitment_id.asc(), Voucher.cycle_number.asc())
        .all()
    ):
        vouchers_by_commitment[row.commitment_id].append(row)

    member_ids = {
        member.user_id
        for rows in members_by_commitment.values()
        for member in rows
    }
    users_by_id = {
        user.id: user
        for user in db.query(User).filter(User.id.in_(member_ids)).all()
    } if member_ids else {}
    vendor_ids = {commitment.vendor_id for commitment in commitments}
    vendors_by_id = {
        vendor.id: vendor
        for vendor in db.query(Vendor).filter(Vendor.id.in_(vendor_ids)).all()
    } if vendor_ids else {}

    return [
        _serialize_commitment_with_relations(
            commitment,
            members=members_by_commitment[commitment.id],
            beneficiaries=beneficiaries_by_commitment[commitment.id],
            contributions=contributions_by_commitment[commitment.id],
            vouchers=vouchers_by_commitment[commitment.id],
            users_by_id=users_by_id,
            vendor=vendors_by_id.get(commitment.vendor_id),
        )
        for commitment in commitments
    ]


def _serialize_commitment_with_relations(
    commitment: Commitment,
    *,
    members: list[CommitmentMember],
    beneficiaries: list[CommitmentBeneficiary],
    contributions: list[Contribution],
    vouchers: list[Voucher],
    users_by_id: dict[str, User],
    vendor: Vendor | None,
) -> dict[str, Any]:
    economic_members = [member for member in members if member.role not in {"replaced", "declined"}]
    member_ids = [member.user_id for member in members]

    current_cycle_contributions = [
        contribution
        for contribution in contributions
        if contribution.cycle_number == commitment.current_cycle_number
    ]
    current_member_totals = {
        member_id: sum(
            contribution.amount
            for contribution in current_cycle_contributions
            if contribution.user_id == member_id
        )
        for member_id in member_ids
    }
    required_cycle_total = commitment.contribution_amount * len(economic_members)
    current_cycle_total = sum(current_member_totals.values())
    current_beneficiary = next(
        (item for item in beneficiaries if item.cycle_number == commitment.current_cycle_number),
        None,
    )

    return {
        "commitment_id": commitment.id,
        "type": commitment.type,
        "title": commitment.title,
        "vendor_id": commitment.vendor_id,
        "vendor": {
            "vendor_id": commitment.vendor_id,
            "name": vendor.name if vendor is not None else None,
            "category": vendor.category if vendor is not None else None,
            "verified": bool(vendor and vendor.verified_at),
        },
        "contribution_amount": commitment.contribution_amount,
        "contribution_frequency": commitment.frequency,
        "first_cycle_due_at": commitment.first_cycle_due_at.isoformat() if commitment.first_cycle_due_at else None,
        "current_cycle_due_at": commitment.current_cycle_due_at.isoformat() if commitment.current_cycle_due_at else None,
        "grace_period_hours": commitment.grace_period_hours,
        "missed_cycle_policy": commitment.missed_cycle_policy,
        "missed_cycle_count": commitment.missed_cycle_count,
        "cycles": commitment.cycles,
        "status": commitment.status,
        "invite_code": commitment.invite_code,
        "current_cycle_number": commitment.current_cycle_number,
        "completed_cycle_count": commitment.completed_cycle_count,
        "payout_order": json.loads(commitment.payout_order_json),
        "cycle_states": [
            {
                "cycle_number": beneficiary.cycle_number,
                "beneficiary_id": beneficiary.user_id,
                "beneficiary_first_name": _first_name(users_by_id.get(beneficiary.user_id)),
                "payout_amount": beneficiary.payout_amount,
                "status": beneficiary.status,
                "due_at": (
                    commitment.current_cycle_due_at.isoformat()
                    if beneficiary.cycle_number == commitment.current_cycle_number and commitment.current_cycle_due_at
                    else None
                ),
                "contributions": [
                    {
                        "id": contribution.id,
                        "event_id": contribution.event_id,
                        "user_id": contribution.user_id,
                        "member_first_name": _first_name(users_by_id.get(contribution.user_id)),
                        "amount": contribution.amount,
                        "paid_at": contribution.paid_at.isoformat() if contribution.paid_at else None,
                    }
                    for contribution in contributions
                    if contribution.cycle_number == beneficiary.cycle_number
                ],
            }
            for beneficiary in beneficiaries
        ],
        "members": [
            {
                "user_id": member.user_id,
                "first_name": _first_name(users_by_id.get(member.user_id)),
                "role": member.role,
                "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                "declined_at": member.declined_at.isoformat() if member.declined_at else None,
                "current_cycle_contribution_total": current_member_totals[member.user_id],
                "current_cycle_payment_status": (
                    "paid"
                    if current_member_totals[member.user_id] >= commitment.contribution_amount
                    else "partial"
                    if current_member_totals[member.user_id] > 0
                    else "not_paid"
                ),
            }
            for member in members
        ],
        "beneficiaries": [
            {
                "id": beneficiary.id,
                "cycle_number": beneficiary.cycle_number,
                "user_id": beneficiary.user_id,
                "first_name": _first_name(users_by_id.get(beneficiary.user_id)),
                "payout_amount": beneficiary.payout_amount,
                "status": beneficiary.status,
            }
            for beneficiary in beneficiaries
        ],
        "contributions": [
            {
                "id": contribution.id,
                "cycle_number": contribution.cycle_number,
                "user_id": contribution.user_id,
                "member_first_name": _first_name(users_by_id.get(contribution.user_id)),
                "amount": contribution.amount,
                "status": contribution.status,
                "rule_trace": json.loads(contribution.rule_trace_json),
                "paid_at": contribution.paid_at.isoformat() if contribution.paid_at else None,
            }
            for contribution in contributions
        ],
        "vouchers": [_serialize_voucher_state(voucher) for voucher in vouchers],
        "current_cycle": {
            "cycle_number": commitment.current_cycle_number,
            "required_total": required_cycle_total,
            "contributed_total": current_cycle_total,
            "remaining_total": max(0, required_cycle_total - current_cycle_total),
            "paid_member_count": sum(
                total >= commitment.contribution_amount for total in current_member_totals.values()
            ),
            "member_count": len(economic_members),
            "progress_percent": (
                min(100, round((current_cycle_total / required_cycle_total) * 100))
                if required_cycle_total
                else 0
            ),
            "beneficiary_id": current_beneficiary.user_id if current_beneficiary else None,
            "beneficiary_first_name": (
                _first_name(users_by_id.get(current_beneficiary.user_id)) if current_beneficiary else None
            ),
        },
    }


def create_commitment(
    db: Session, payload: LockRequest, authenticated_creator_id: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    payload.first_cycle_due_at = _normalize_due_at(payload.first_cycle_due_at)
    if payload.type != "rotating":
        raise HTTPException(status_code=400, detail="Only rotating commitments are supported.")
    if not payload.members:
        raise HTTPException(status_code=400, detail="At least one member is required.")
    if payload.contribution_amount <= 0:
        raise HTTPException(status_code=400, detail="Contribution amount must be positive.")
    if payload.cycles <= 0:
        raise HTTPException(status_code=400, detail="Cycles must be positive.")
    if payload.contribution_frequency not in SUPPORTED_FREQUENCIES:
        raise HTTPException(status_code=400, detail="Contribution frequency must be daily, weekly, or monthly.")
    if payload.first_cycle_due_at is not None and payload.first_cycle_due_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="first_cycle_due_at must be in the future.")

    member_ids = _normalize_member_ids(payload.members)
    if payload.creator_id and payload.creator_id != authenticated_creator_id:
        raise HTTPException(status_code=403, detail="creator_id must match the authenticated user.")
    creator_id = authenticated_creator_id
    if creator_id not in member_ids:
        member_ids = _normalize_member_ids([creator_id, *member_ids])
    _require_rotating_group_size(member_ids)
    if payload.cycles != len(member_ids):
        raise HTTPException(
            status_code=400,
            detail="A rotating commitment must have one cycle per member.",
        )

    try:
        with db.begin():
            for member_id in member_ids:
                _ensure_member_user(db, member_id)
            _require_score_processing_consent(db, creator_id)
            vendor = db.get(Vendor, payload.vendor_id)
            if vendor is None or vendor.verified_at is None:
                raise HTTPException(status_code=400, detail="Commitment vendor must be verified before it can be locked.")
            db.flush()

            payout_order, genesis_group = _build_payout_order(db, member_ids, payload.payout_order)
            payout_schedule = build_payout_schedule(payout_order, payload.contribution_amount, payload.cycles)
            if payout_schedule and genesis_group:
                capped_amount = apply_anchor_and_cap_rule(payout_schedule[0]["amount"], 1)
                if capped_amount != payout_schedule[0]["amount"]:
                    raise HTTPException(
                        status_code=400,
                        detail="Genesis commitments must keep the first pooled payout within the configured cap.",
                    )

            commitment = Commitment(
                id=str(uuid.uuid4()),
                creator_id=creator_id,
                type=payload.type,
                title=payload.title,
                vendor_id=payload.vendor_id,
                contribution_amount=payload.contribution_amount,
                frequency=payload.contribution_frequency,
                cycles=payload.cycles,
                status="pending_members",
                invite_code=f"SURA-{uuid.uuid4().hex[:8].upper()}",
                payout_order_json=json.dumps(payout_order),
                current_cycle_number=1,
                completed_cycle_count=0,
                first_cycle_due_at=payload.first_cycle_due_at or default_first_due_at(payload.contribution_frequency, datetime.utcnow()),
                grace_period_hours=payload.grace_period_hours,
                missed_cycle_policy=payload.missed_cycle_policy,
            )
            db.add(commitment)
            db.flush()

            for member_id in member_ids:
                db.add(
                    CommitmentMember(
                        commitment_id=commitment.id,
                        user_id=member_id,
                        role="creator" if member_id == creator_id else "invited",
                        joined_at=datetime.utcnow(),
                    )
                )

            # A one-member rotating commitment has no invitations to accept.
            # Activate it immediately so its first contribution is valid.
            _activate_if_fully_joined(db, commitment)

            for cycle in payout_schedule:
                db.add(
                    CommitmentBeneficiary(
                        id=str(uuid.uuid4()),
                        commitment_id=commitment.id,
                        cycle_number=cycle["cycle"],
                        user_id=cycle["beneficiary_id"],
                        payout_amount=cycle["amount"],
                        status="scheduled",
                    )
                )

            _record_activity(
                db,
                commitment.id,
                "commitment_created",
                actor_user_id=creator_id,
                details={
                    "title": commitment.title,
                    "vendor_id": commitment.vendor_id,
                    "member_count": len(member_ids),
                    "missed_cycle_policy": commitment.missed_cycle_policy,
                },
            )

            return _serialize_commitment(commitment, db), {
                "commitment_id": commitment.id,
                "type": commitment.type,
                "status": commitment.status,
                "invite_code": commitment.invite_code,
                "payout_schedule": payout_schedule,
            }
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create commitment.") from exc


def _refresh_score_history_for_commitment(
    db: Session,
    commitment_id: str,
    event_id: str | None = None,
    event_type: str = "contribution_processed",
    reason: str = "contribution_processed",
) -> None:
    refresh_commitment_member_scores(
        db,
        commitment_id,
        event_id=event_id,
        event_type=event_type,
        reason=reason,
    )


def record_contribution(
    db: Session,
    commitment_id: str,
    contributor_user_id: str,
    payload: ContributionRequest,
) -> dict[str, Any]:
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Contribution amount must be positive.")

    try:
        with db.begin():
            commitment = (
                db.query(Commitment)
                .filter(Commitment.id == commitment_id)
                .with_for_update()
                .one_or_none()
            )
            if commitment is None:
                raise HTTPException(status_code=404, detail="Commitment not found.")
            _refresh_lifecycle(db, commitment)
            member = _require_member(db, commitment_id, contributor_user_id)
            if member.role == "invited":
                raise HTTPException(status_code=400, detail="Join this commitment before contributing.")

            # Membership is checked first so a non-member still gets the 403 that
            # says nothing about whether they could contribute, rather than a 403
            # that reveals the account is under bank review.
            risk_rules.assert_can_transact(db, contributor_user_id)

            prior_event = (
                db.query(Contribution)
                .filter(
                    Contribution.commitment_id == commitment_id,
                    Contribution.user_id == contributor_user_id,
                    Contribution.event_id == payload.event_id,
                )
                .one_or_none()
            )
            if prior_event is not None:
                if prior_event.amount != payload.amount:
                    raise HTTPException(
                        status_code=409,
                        detail="event_id was already used with a different contribution amount.",
                    )
                response = _serialize_commitment(commitment, db)
                response.update(
                    {
                        "idempotent_replay": True,
                        "event_id": prior_event.event_id,
                        "contribution_status": prior_event.status,
                        "rule_trace": json.loads(prior_event.rule_trace_json),
                    }
                )
                # A replay must answer with the same shape as the original call, so
                # the client's success path does not have to special-case retries.
                response["score"] = public_score_report(db, contributor_user_id)
                return response

            if commitment.status not in {"active", "overdue", "missed"}:
                raise HTTPException(status_code=400, detail="Commitment is not accepting contributions.")

            current_cycle = commitment.current_cycle_number
            member_total_before = (
                db.query(Contribution)
                .filter(
                    Contribution.commitment_id == commitment_id,
                    Contribution.cycle_number == current_cycle,
                    Contribution.user_id == contributor_user_id,
                )
                .with_entities(func.coalesce(func.sum(Contribution.amount), 0))
                .scalar()
            )
            cycle_total_before = (
                db.query(Contribution)
                .filter(
                    Contribution.commitment_id == commitment_id,
                    Contribution.cycle_number == current_cycle,
                )
                .with_entities(func.coalesce(func.sum(Contribution.amount), 0))
                .scalar()
            )
            required_cycle_total = commitment.contribution_amount * db.query(CommitmentMember).filter(
                CommitmentMember.commitment_id == commitment_id,
                CommitmentMember.role.in_(("creator", "contributor")),
            ).count()
            allows_shortfall_cover = (
                commitment.status == "missed"
                and commitment.missed_cycle_policy == "cover_shortfall"
                and member_total_before >= commitment.contribution_amount
                and cycle_total_before < required_cycle_total
            )
            if allows_shortfall_cover:
                remaining = required_cycle_total - cycle_total_before
                if payload.amount > remaining:
                    raise HTTPException(status_code=400, detail="Contribution exceeds the remaining cycle shortfall.")
            elif payload.amount > commitment.contribution_amount:
                raise HTTPException(status_code=400, detail="Contribution amount cannot exceed the commitment amount.")
            if member_total_before >= commitment.contribution_amount and not allows_shortfall_cover:
                raise HTTPException(status_code=400, detail="This member has already completed the current cycle contribution.")
            if not allows_shortfall_cover and member_total_before + payload.amount > commitment.contribution_amount:
                raise HTTPException(status_code=400, detail="Contribution exceeds the member's remaining amount for this cycle.")

            contribution_row = Contribution(
                id=str(uuid.uuid4()),
                commitment_id=commitment_id,
                cycle_number=current_cycle,
                user_id=contributor_user_id,
                amount=payload.amount,
                event_id=payload.event_id,
                status="shortfall_cover" if allows_shortfall_cover else "full" if payload.amount == commitment.contribution_amount else "partial",
                rule_trace_json="{}",
                paid_at=datetime.utcnow(),
            )
            db.add(contribution_row)
            db.flush()

            member_count = db.query(CommitmentMember).filter(
                CommitmentMember.commitment_id == commitment_id,
                CommitmentMember.role.in_(("creator", "contributor")),
            ).count()
            contributions_for_cycle = (
                db.query(Contribution)
                .filter(Contribution.commitment_id == commitment_id, Contribution.cycle_number == current_cycle)
                .all()
            )
            distinct_contributors = len({row.user_id for row in contributions_for_cycle})
            # The engine derives its own running totals from the two "before"
            # values, so they are not computed again here.
            evaluation = evaluate_contribution(
                contribution_amount=payload.amount,
                expected_member_amount=commitment.contribution_amount,
                member_total_before=member_total_before,
                cycle_total_before=cycle_total_before,
                member_count=member_count,
                distinct_contributors=distinct_contributors,
                allows_shortfall_cover=allows_shortfall_cover,
            )

            # The row inserted just above is already in hand, so the engine's verdict
            # is written back to it directly. Re-querying for "the latest contribution
            # by this member this cycle" could match a different row, and on a
            # re-sent request it would rewrite history rather than this attempt.
            contribution_row.status = evaluation.contribution_status
            contribution_row.rule_trace_json = dump_rule_trace(evaluation)
            _record_activity(
                db,
                commitment_id,
                "contribution_recorded",
                actor_user_id=contributor_user_id,
                cycle_number=current_cycle,
                details={"amount": payload.amount, "status": evaluation.contribution_status, "event_id": payload.event_id},
            )

            beneficiary_row = (
                db.query(CommitmentBeneficiary)
                .filter(
                    CommitmentBeneficiary.commitment_id == commitment_id,
                    CommitmentBeneficiary.cycle_number == current_cycle,
                )
                .one_or_none()
            )

            if evaluation.cycle_complete:
                was_missed = commitment.status == "missed" or (beneficiary_row is not None and beneficiary_row.status == "missed")
                if beneficiary_row is not None:
                    beneficiary_row.status = "paid"
                    _record_activity(
                        db,
                        commitment_id,
                        "cycle_recovered" if was_missed else "cycle_paid",
                        cycle_number=current_cycle,
                        details={
                            "beneficiary_id": beneficiary_row.user_id,
                            "amount": beneficiary_row.payout_amount,
                            "recovered": was_missed,
                        },
                    )
                    _issue_voucher_if_needed(db, commitment, beneficiary_row)

                commitment.completed_cycle_count += 1
                if current_cycle >= commitment.cycles:
                    commitment.status = "completed"
                else:
                    commitment.current_cycle_number = current_cycle + 1
                    commitment.status = "active"
                    commitment.current_cycle_due_at = advance_due_at(
                        commitment.current_cycle_due_at or commitment.first_cycle_due_at,
                        commitment.frequency,
                    )
            else:
                _refresh_lifecycle(db, commitment)

            _refresh_score_history_for_commitment(
                db,
                commitment_id,
                event_id=payload.event_id,
                reason="contribution_processed",
            )

            # Same session, same identity map, so this is the row already mutated
            # above and re-reading it would only ever return the same instance.
            response = _serialize_commitment(commitment, db)
            response.update(
                {
                    "status": commitment.status,
                    "contribution_status": evaluation.contribution_status,
                    "event_id": payload.event_id,
                    "idempotent_replay": False,
                    "cycle_status": evaluation.cycle_status,
                    "completed_cycle": evaluation.cycle_complete,
                    "beneficiary": None,
                    "updated_at": datetime.utcnow().isoformat(),
                    "rule_trace": evaluation.to_rule_trace(),
                }
            )
            if beneficiary_row is not None:
                response["beneficiary"] = {
                    "cycle_number": beneficiary_row.cycle_number,
                    "user_id": beneficiary_row.user_id,
                    "payout_amount": beneficiary_row.payout_amount,
                    "status": beneficiary_row.status,
                }
            # The score moves because of this contribution, so the caller gets the new
            # one back here instead of spending a second round trip on /v1/score.
            response["score"] = public_score_report(db, contributor_user_id)
            return response
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to record contribution.") from exc


def get_commitment_details(db: Session, commitment_id: str, requester_user_id: str) -> dict[str, Any]:
    commitment = db.get(Commitment, commitment_id)
    if commitment is None:
        raise HTTPException(status_code=404, detail="Commitment not found.")
    _require_member(db, commitment_id, requester_user_id)
    if _refresh_lifecycle(db, commitment):
        db.commit()
    return _serialize_commitment(commitment, db)


def list_member_commitments(db: Session, user_id: str) -> list[dict[str, Any]]:
    commitments = (
        db.query(Commitment)
        .join(CommitmentMember, CommitmentMember.commitment_id == Commitment.id)
        .filter(CommitmentMember.user_id == user_id)
        .order_by(Commitment.created_at.desc(), Commitment.id.desc())
        .all()
    )
    changed = any(_refresh_lifecycle(db, commitment) for commitment in commitments)
    if changed:
        db.commit()
    return _serialize_commitments(commitments, db)


def preview_commitment_by_code(db: Session, invite_code: str, user_id: str) -> dict[str, Any]:
    commitment = db.query(Commitment).filter(Commitment.invite_code == invite_code).one_or_none()
    if commitment is None or commitment.status == "cancelled":
        raise HTTPException(status_code=404, detail="Commitment invite was not found.")
    member = _require_member(db, commitment.id, user_id)
    preview = _serialize_commitment(commitment, db)
    preview["join_status"] = "joined" if member.role != "invited" else "invited"
    return preview


def join_commitment(db: Session, invite_code: str, user_id: str) -> dict[str, Any]:
    with db.begin():
        _require_score_processing_consent(db, user_id)
        commitment = (
            db.query(Commitment)
            .filter(Commitment.invite_code == invite_code)
            .with_for_update()
            .one_or_none()
        )
        if commitment is None or commitment.status == "cancelled":
            raise HTTPException(status_code=404, detail="Commitment invite was not found.")
        if commitment.status not in {"pending_members", "active"}:
            raise HTTPException(status_code=400, detail="This commitment is no longer accepting members.")
        member = _require_member(db, commitment.id, user_id)
        if member.role == "invited":
            member.role = "contributor"
            member.joined_at = datetime.utcnow()
            _record_activity(
                db,
                commitment.id,
                "member_joined",
                actor_user_id=user_id,
                details={"user_id": user_id},
            )
            _activate_if_fully_joined(db, commitment)
        elif member.role != "contributor" and member.role != "creator":
            raise HTTPException(status_code=400, detail="This invitation is no longer available. Ask the creator for a replacement invite.")
        response = _serialize_commitment(commitment, db)
        response["join_status"] = "joined"
        return response


def record_score_consent(db: Session, user_id: str, granted: bool) -> dict[str, Any]:
    with db.begin():
        consent = (
            db.query(UserConsent)
            .filter(UserConsent.user_id == user_id, UserConsent.consent_type == "score_processing")
            .one_or_none()
        )
        if consent is None:
            consent = UserConsent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                consent_type="score_processing",
                granted=granted,
                recorded_at=datetime.utcnow(),
            )
            db.add(consent)
        else:
            consent.granted = granted
            consent.recorded_at = datetime.utcnow()
        db.flush()
        # The invite flow can collect consent before its placeholder account is
        # materialised. Preserve that flow and only create a snapshot for a
        # real account.
        if consent.granted and db.get(User, user_id) is not None:
            record_score_snapshot(
                db,
                user_id,
                event_type="score_consent_granted",
                reason="Member granted score-processing consent.",
                source_id=consent.id,
            )
        return {
            "user_id": user_id,
            "consent_type": consent.consent_type,
            "granted": consent.granted,
            "recorded_at": consent.recorded_at.isoformat() if consent.recorded_at else None,
        }


def get_commitment_activity(db: Session, commitment_id: str, requester_user_id: str) -> list[dict[str, Any]]:
    _require_member(db, commitment_id, requester_user_id)
    activity_rows = (
        db.query(CommitmentActivity)
        .filter(CommitmentActivity.commitment_id == commitment_id)
        .order_by(CommitmentActivity.occurred_at.asc(), CommitmentActivity.id.asc())
        .all()
    )
    return [
        {
            "id": item.id,
            "event_type": item.event_type,
            "actor_user_id": item.actor_user_id,
            "cycle_number": item.cycle_number,
            "details": json.loads(item.detail_json),
            "occurred_at": item.occurred_at.isoformat() if item.occurred_at else None,
        }
        for item in activity_rows
    ]


def cancel_pending_commitment(db: Session, commitment_id: str, requester_user_id: str) -> dict[str, Any]:
    with db.begin():
        commitment = (
            db.query(Commitment)
            .filter(Commitment.id == commitment_id)
            .with_for_update()
            .one_or_none()
        )
        if commitment is None:
            raise HTTPException(status_code=404, detail="Commitment not found.")
        if commitment.creator_id != requester_user_id:
            raise HTTPException(status_code=403, detail="Only the commitment creator can cancel it.")
        if commitment.status != "pending_members":
            raise HTTPException(status_code=400, detail="Only pending commitments can be cancelled.")
        commitment.status = "cancelled"
        _record_activity(db, commitment_id, "commitment_cancelled", actor_user_id=requester_user_id)
        return _serialize_commitment(commitment, db)


def open_commitment_case(db: Session, commitment_id: str, bank_id: str, actor_id: str, reason: str) -> dict[str, Any]:
    """Pause a disputed Lock without changing membership, amounts, or payout order."""
    with db.begin():
        commitment = db.query(Commitment).filter(Commitment.id == commitment_id).with_for_update().one_or_none()
        if commitment is None:
            raise HTTPException(status_code=404, detail="Commitment not found.")
        creator = db.get(User, commitment.creator_id)
        if creator is None or creator.bank_id != bank_id:
            raise HTTPException(status_code=404, detail="Commitment not found for this bank.")
        if db.query(CommitmentCase).filter(
            CommitmentCase.commitment_id == commitment_id,
            CommitmentCase.bank_id == bank_id,
            CommitmentCase.status == "open",
        ).one_or_none() is not None:
            raise HTTPException(status_code=409, detail="An open support case already exists for this commitment.")
        case = CommitmentCase(
            id=str(uuid.uuid4()), commitment_id=commitment_id, bank_id=bank_id,
            opened_by=actor_id, reason=reason.strip(), status="open", opened_at=datetime.utcnow(),
        )
        db.add(case)
        previous_status = commitment.status
        commitment.status = "under_review"
        _record_activity(
            db, commitment_id, "commitment_under_review", actor_user_id=actor_id,
            cycle_number=commitment.current_cycle_number,
            details={"case_id": case.id, "previous_status": previous_status},
        )
        return {"case_id": case.id, "commitment_id": commitment_id, "status": "open", "commitment_status": "under_review"}


def resolve_commitment_case(db: Session, commitment_id: str, bank_id: str, actor_id: str, case_id: str, note: str) -> dict[str, Any]:
    with db.begin():
        case = db.query(CommitmentCase).filter(
            CommitmentCase.id == case_id,
            CommitmentCase.commitment_id == commitment_id,
            CommitmentCase.bank_id == bank_id,
        ).with_for_update().one_or_none()
        if case is None:
            raise HTTPException(status_code=404, detail="Support case not found.")
        if case.status != "open":
            raise HTTPException(status_code=400, detail="Support case is already resolved.")
        commitment = db.query(Commitment).filter(Commitment.id == commitment_id).with_for_update().one()
        case.status = "resolved"
        case.resolution_note = note.strip()
        case.resolved_by = actor_id
        case.resolved_at = datetime.utcnow()
        commitment.status = "active"
        _refresh_lifecycle(db, commitment)
        _record_activity(
            db, commitment_id, "commitment_review_resolved", actor_user_id=actor_id,
            cycle_number=commitment.current_cycle_number, details={"case_id": case.id},
        )
        return {"case_id": case.id, "commitment_id": commitment_id, "status": "resolved", "commitment_status": commitment.status}


def decline_commitment_invitation(db: Session, commitment_id: str, requester_user_id: str) -> dict[str, Any]:
    with db.begin():
        commitment = db.query(Commitment).filter(Commitment.id == commitment_id).with_for_update().one_or_none()
        if commitment is None:
            raise HTTPException(status_code=404, detail="Commitment not found.")
        if commitment.status != "pending_members":
            raise HTTPException(status_code=400, detail="Only pending commitment invitations may be declined.")
        member = _require_member(db, commitment_id, requester_user_id)
        if member.role != "invited":
            raise HTTPException(status_code=400, detail="Only an invited member may decline this commitment.")
        member.role = "declined"
        member.declined_at = datetime.utcnow()
        _record_activity(
            db,
            commitment_id,
            "member_declined",
            actor_user_id=requester_user_id,
            details={"user_id": requester_user_id},
        )
        return _serialize_commitment(commitment, db)


def replace_pending_member(
    db: Session,
    commitment_id: str,
    creator_user_id: str,
    invited_user_id: str,
    replacement_user_id: str,
) -> dict[str, Any]:
    """Replace only an unresolved invitation before activation.

    A paid or active group cannot change membership because that would change
    the agreed pool and payout order.
    """
    with db.begin():
        commitment = db.query(Commitment).filter(Commitment.id == commitment_id).with_for_update().one_or_none()
        if commitment is None:
            raise HTTPException(status_code=404, detail="Commitment not found.")
        if commitment.creator_id != creator_user_id:
            raise HTTPException(status_code=403, detail="Only the commitment creator can replace an invitee.")
        if commitment.status != "pending_members":
            raise HTTPException(status_code=400, detail="Members cannot be replaced after commitment activation.")
        if invited_user_id == replacement_user_id:
            raise HTTPException(status_code=400, detail="Replacement member must be different from the existing invitee.")
        old_member = _require_member(db, commitment_id, invited_user_id)
        if old_member.role not in {"invited", "declined"}:
            raise HTTPException(status_code=400, detail="Only unresolved invitations may be replaced.")
        if db.query(CommitmentMember).filter(
            CommitmentMember.commitment_id == commitment_id,
            CommitmentMember.user_id == replacement_user_id,
        ).one_or_none() is not None:
            raise HTTPException(status_code=409, detail="Replacement user is already part of this commitment.")
        _ensure_member_user(db, replacement_user_id)
        _require_score_processing_consent(db, replacement_user_id)
        old_member.role = "replaced"
        old_member.declined_at = datetime.utcnow()
        db.add(CommitmentMember(
            commitment_id=commitment_id,
            user_id=replacement_user_id,
            role="invited",
            joined_at=datetime.utcnow(),
        ))
        payout_order = json.loads(commitment.payout_order_json)
        commitment.payout_order_json = json.dumps([
            replacement_user_id if user_id == invited_user_id else user_id for user_id in payout_order
        ])
        db.query(CommitmentBeneficiary).filter(
            CommitmentBeneficiary.commitment_id == commitment_id,
            CommitmentBeneficiary.user_id == invited_user_id,
        ).update({CommitmentBeneficiary.user_id: replacement_user_id}, synchronize_session=False)
        _record_activity(
            db,
            commitment_id,
            "member_replaced",
            actor_user_id=creator_user_id,
            details={"replaced_user_id": invited_user_id, "replacement_user_id": replacement_user_id},
        )
        return _serialize_commitment(commitment, db)


def get_cycle_voucher(
    db: Session, commitment_id: str, cycle_number: int, requester_user_id: str
) -> dict[str, Any]:
    with db.begin():
        commitment = db.get(Commitment, commitment_id)
        if commitment is None:
            raise HTTPException(status_code=404, detail="Commitment not found.")
        _require_member(db, commitment_id, requester_user_id)
        beneficiary = (
            db.query(CommitmentBeneficiary)
            .filter(
                CommitmentBeneficiary.commitment_id == commitment_id,
                CommitmentBeneficiary.cycle_number == cycle_number,
            )
            .one_or_none()
        )
        if beneficiary is None:
            raise HTTPException(status_code=404, detail="Cycle not found.")
        if beneficiary.user_id != requester_user_id:
            raise HTTPException(status_code=403, detail="Only this cycle's beneficiary may view its voucher.")
        vendor = db.get(Vendor, commitment.vendor_id)
        voucher = (
            db.query(Voucher)
            .filter(Voucher.commitment_id == commitment_id, Voucher.cycle_number == cycle_number)
            .one_or_none()
        )
        if voucher is not None:
            response = _serialize_voucher(voucher)
            response["vendor_name"] = vendor.name if vendor is not None else None
            # Sura Lock does not currently model voucher expiry. An explicit null
            # prevents clients from inventing a deadline that the backend cannot enforce.
            response["expires_at"] = None
            return response
        if beneficiary.status == "paid":
            voucher = _issue_voucher_if_needed(db, commitment, beneficiary)
            db.flush()
            response = _serialize_voucher(voucher)
            response["vendor_name"] = vendor.name if vendor is not None else None
            response["expires_at"] = None
            return response
        if beneficiary.status == "redeemed":
            redemption = (
                db.query(Redemption)
                .filter(Redemption.commitment_id == commitment_id, Redemption.cycle_number == cycle_number)
                .one_or_none()
            )
            if redemption is not None:
                return {
                    "commitment_id": commitment_id,
                    "beneficiary_id": beneficiary.user_id,
                    "vendor_id": redemption.vendor_id,
                    "vendor_name": vendor.name if vendor is not None else None,
                    "cycle_number": cycle_number,
                    "amount": redemption.amount,
                    "voucher_code": redemption.voucher_code,
                    "status": "redeemed",
                    "issued_at": None,
                    "redeemed_at": redemption.redeemed_at.isoformat() if redemption.redeemed_at else None,
                    "expires_at": None,
                }
        return {
            "commitment_id": commitment_id,
            "beneficiary_id": beneficiary.user_id,
            "vendor_id": commitment.vendor_id,
            "vendor_name": vendor.name if vendor is not None else None,
            "cycle_number": cycle_number,
            "amount": beneficiary.payout_amount,
            "voucher_code": None,
            "status": "locked",
            "issued_at": None,
            "redeemed_at": None,
            "expires_at": None,
        }


def validate_vendor_voucher(db: Session, voucher_code: str, vendor_id: str) -> dict[str, Any]:
    voucher = db.query(Voucher).filter(Voucher.code == voucher_code).one_or_none()
    if voucher is None:
        raise HTTPException(status_code=404, detail="Voucher is invalid.")
    if voucher.vendor_id != vendor_id:
        raise HTTPException(status_code=403, detail="Voucher is locked to a different vendor.")
    if voucher.status == "redeemed":
        raise HTTPException(status_code=409, detail="Voucher has already been redeemed.")
    if voucher.status != "ready":
        raise HTTPException(status_code=400, detail="Voucher is not ready for redemption.")
    commitment = db.get(Commitment, voucher.commitment_id)
    if commitment is not None and commitment.status == "under_review":
        raise HTTPException(status_code=409, detail="Commitment redemption is paused while a support case is under review.")
    beneficiary = db.get(User, voucher.beneficiary_id)
    return {
        "voucher": _serialize_voucher(voucher),
        "commitment_title": commitment.title if commitment else None,
        "beneficiary_first_name": beneficiary.name.split(maxsplit=1)[0] if beneficiary else None,
    }


def redeem_vendor_voucher(db: Session, voucher_code: str, vendor_id: str) -> dict[str, Any]:
    with db.begin():
        voucher = (
            db.query(Voucher)
            .filter(Voucher.code == voucher_code)
            .with_for_update()
            .one_or_none()
        )
        if voucher is None:
            raise HTTPException(status_code=404, detail="Voucher is invalid.")
        if voucher.vendor_id != vendor_id:
            raise HTTPException(status_code=403, detail="Voucher is locked to a different vendor.")
        if voucher.status == "redeemed":
            raise HTTPException(status_code=409, detail="Voucher has already been redeemed.")
        if voucher.status != "ready":
            raise HTTPException(status_code=400, detail="Voucher is not ready for redemption.")
        commitment = db.get(Commitment, voucher.commitment_id)
        if commitment is not None and commitment.status == "under_review":
            raise HTTPException(status_code=409, detail="Commitment redemption is paused while a support case is under review.")
        beneficiary = (
            db.query(CommitmentBeneficiary)
            .filter(
                CommitmentBeneficiary.commitment_id == voucher.commitment_id,
                CommitmentBeneficiary.cycle_number == voucher.cycle_number,
            )
            .one_or_none()
        )
        if beneficiary is None or beneficiary.status != "paid":
            raise HTTPException(status_code=400, detail="Voucher cycle is not ready for redemption.")
        # The beneficiary is the person the money is paid out to, so a
        # restriction stops the payout as well as new contributions. Locking the
        # row first means the status check and the redemption cannot race.
        risk_rules.assert_can_transact(db, voucher.beneficiary_id)
        redemption = Redemption(
            id=str(uuid.uuid4()),
            commitment_id=voucher.commitment_id,
            beneficiary_id=voucher.beneficiary_id,
            vendor_id=voucher.vendor_id,
            cycle_number=voucher.cycle_number,
            amount=voucher.amount,
            voucher_code=voucher.code,
            status="settled",
            redeemed_at=datetime.utcnow(),
        )
        db.add(redemption)
        beneficiary.status = "redeemed"
        voucher.status = "redeemed"
        voucher.redeemed_at = redemption.redeemed_at
        _record_activity(
            db,
            voucher.commitment_id,
            "voucher_redeemed",
            actor_user_id=None,
            cycle_number=voucher.cycle_number,
            # Activity is visible to every commitment member. The voucher code
            # is a redemption credential and must only appear in the
            # beneficiary and authenticated-vendor flows.
            details={"vendor_id": vendor_id, "amount": voucher.amount},
        )
        beneficiary_user = db.get(User, voucher.beneficiary_id)
        return {
            "redemption_id": redemption.id,
            "commitment_id": voucher.commitment_id,
            "vendor_id": redemption.vendor_id,
            "cycle_number": redemption.cycle_number,
            "amount": redemption.amount,
            "voucher_code": voucher.code,
            "status": redemption.status,
            "redeemed_at": redemption.redeemed_at.isoformat() if redemption.redeemed_at else None,
            "commitment_title": commitment.title if commitment is not None else None,
            "beneficiary_first_name": _first_name(beneficiary_user),
        }


def _serialize_vendor_redemption(
    redemption: Redemption,
    *,
    commitment: Commitment | None,
    beneficiary: User | None,
) -> dict[str, Any]:
    """A merchant receipt: no score, phone number, or unrelated user data."""
    return {
        "redemption_id": redemption.id,
        "commitment_id": redemption.commitment_id,
        "commitment_title": commitment.title if commitment is not None else None,
        "beneficiary_id": redemption.beneficiary_id,
        "beneficiary_first_name": _first_name(beneficiary),
        "cycle_number": redemption.cycle_number,
        "amount": redemption.amount,
        "voucher_code": redemption.voucher_code,
        "status": redemption.status,
        "redeemed_at": redemption.redeemed_at.isoformat() if redemption.redeemed_at else None,
    }


def list_vendor_redemptions(db: Session, vendor_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(Redemption)
        .filter(Redemption.vendor_id == vendor_id)
        .order_by(Redemption.redeemed_at.desc(), Redemption.id.desc())
        .all()
    )
    commitments_by_id = {
        commitment.id: commitment
        for commitment in db.query(Commitment)
        .filter(Commitment.id.in_([row.commitment_id for row in rows]))
        .all()
    } if rows else {}
    beneficiaries_by_id = {
        user.id: user
        for user in db.query(User)
        .filter(User.id.in_([row.beneficiary_id for row in rows]))
        .all()
    } if rows else {}
    return [
        _serialize_vendor_redemption(
            redemption,
            commitment=commitments_by_id.get(redemption.commitment_id),
            beneficiary=beneficiaries_by_id.get(redemption.beneficiary_id),
        )
        for redemption in rows
    ]


def get_vendor_redemption_detail(db: Session, vendor_id: str, redemption_id: str) -> dict[str, Any]:
    """Return one receipt only when it belongs to the authenticated merchant."""
    redemption = (
        db.query(Redemption)
        .filter(Redemption.id == redemption_id, Redemption.vendor_id == vendor_id)
        .one_or_none()
    )
    if redemption is None:
        raise HTTPException(status_code=404, detail="Redemption was not found.")
    return _serialize_vendor_redemption(
        redemption,
        commitment=db.get(Commitment, redemption.commitment_id),
        beneficiary=db.get(User, redemption.beneficiary_id),
    )
