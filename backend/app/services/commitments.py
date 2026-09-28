import json
import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Commitment, CommitmentBeneficiary, CommitmentMember, Contribution, Redemption, ScoreHistory, User, Vendor
from app.schemas import ContributionRequest, LockRequest
from app.services.contribution_engine import dump_rule_trace, evaluate_contribution
from app.services.payout_rules import apply_anchor_and_cap_rule, build_payout_schedule
from app.services.scoring import build_score_snapshot, serialize_score_snapshot

ENTRY_TIER_SCORE = 12


def _normalize_member_ids(member_ids: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for member_id in member_ids:
        if member_id in seen:
            raise HTTPException(status_code=400, detail="Member IDs must be unique.")
        seen.add(member_id)
        normalized.append(member_id)
    return normalized


def _ensure_user(db: Session, user_id: str) -> None:
    if db.get(User, user_id) is not None:
        return

    db.add(
        User(
            id=user_id,
            name=user_id,
            phone=f"demo-{user_id}@sura.local",
        )
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
    scores = _latest_score_by_user(db, member_ids)
    if not scores:
        if requested_order is None:
            raise HTTPException(
                status_code=400,
                detail="Genesis commitments require a payout_order chosen by the group.",
            )
        if len(requested_order) != len(member_ids) or set(requested_order) != set(member_ids):
            raise HTTPException(
                status_code=400,
                detail="payout_order must contain every member exactly once.",
            )
        return requested_order, True

    ranked = sorted(
        enumerate(member_ids),
        key=lambda item: (-scores.get(item[1], ENTRY_TIER_SCORE), item[0]),
    )
    return [member_id for _, member_id in ranked], False


def _serialize_commitment(commitment: Commitment, db: Session) -> dict[str, Any]:
    members = (
        db.query(CommitmentMember)
        .filter(CommitmentMember.commitment_id == commitment.id)
        .order_by(CommitmentMember.joined_at.asc(), CommitmentMember.user_id.asc())
        .all()
    )
    beneficiaries = (
        db.query(CommitmentBeneficiary)
        .filter(CommitmentBeneficiary.commitment_id == commitment.id)
        .order_by(CommitmentBeneficiary.cycle_number.asc())
        .all()
    )
    contributions = (
        db.query(Contribution)
        .filter(Contribution.commitment_id == commitment.id)
        .order_by(Contribution.cycle_number.asc(), Contribution.paid_at.asc(), Contribution.user_id.asc())
        .all()
    )

    return {
        "commitment_id": commitment.id,
        "type": commitment.type,
        "title": commitment.title,
        "vendor_id": commitment.vendor_id,
        "contribution_amount": commitment.contribution_amount,
        "contribution_frequency": commitment.frequency,
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
                "payout_amount": beneficiary.payout_amount,
                "status": beneficiary.status,
                "contributions": [
                    {
                        "id": contribution.id,
                        "event_id": contribution.event_id,
                        "user_id": contribution.user_id,
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
                "role": member.role,
                "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            }
            for member in members
        ],
        "beneficiaries": [
            {
                "id": beneficiary.id,
                "cycle_number": beneficiary.cycle_number,
                "user_id": beneficiary.user_id,
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
                "amount": contribution.amount,
                "status": contribution.status,
                "rule_trace": json.loads(contribution.rule_trace_json),
                "paid_at": contribution.paid_at.isoformat() if contribution.paid_at else None,
            }
            for contribution in contributions
        ],
    }


def create_commitment(
    db: Session, payload: LockRequest, authenticated_creator_id: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    if payload.type != "rotating":
        raise HTTPException(status_code=400, detail="Only rotating commitments are supported.")
    if not payload.members:
        raise HTTPException(status_code=400, detail="At least one member is required.")
    if payload.contribution_amount <= 0:
        raise HTTPException(status_code=400, detail="Contribution amount must be positive.")
    if payload.cycles <= 0:
        raise HTTPException(status_code=400, detail="Cycles must be positive.")

    member_ids = _normalize_member_ids(payload.members)
    if payload.creator_id and payload.creator_id != authenticated_creator_id:
        raise HTTPException(status_code=403, detail="creator_id must match the authenticated user.")
    creator_id = authenticated_creator_id
    if creator_id not in member_ids:
        member_ids = _normalize_member_ids([creator_id, *member_ids])
    if payload.cycles != len(member_ids):
        raise HTTPException(
            status_code=400,
            detail="A rotating commitment must have one cycle per member.",
        )

    try:
        with db.begin():
            for member_id in member_ids:
                _ensure_user(db, member_id)
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
            )
            db.add(commitment)
            db.flush()

            for member_id in member_ids:
                db.add(
                    CommitmentMember(
                        commitment_id=commitment.id,
                        user_id=member_id,
                        role="contributor",
                        joined_at=datetime.utcnow(),
                    )
                )

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


def _refresh_score_history_for_commitment(db: Session, commitment_id: str) -> None:
    commitment = db.get(Commitment, commitment_id)
    if commitment is None:
        return

    members = (
        db.query(CommitmentMember)
        .filter(CommitmentMember.commitment_id == commitment_id)
        .all()
    )
    for member in members:
        contribution_rows = (
            db.query(Contribution)
            .filter(Contribution.commitment_id == commitment_id, Contribution.user_id == member.user_id)
            .all()
        )
        member_cycle_totals: dict[int, int] = {}
        for row in contribution_rows:
            member_cycle_totals[row.cycle_number] = member_cycle_totals.get(row.cycle_number, 0) + row.amount
        contribution_points = [
            10 if total >= commitment.contribution_amount else 4
            for total in member_cycle_totals.values()
        ]
        completed_cycles = (
            db.query(CommitmentBeneficiary)
            .filter(
                CommitmentBeneficiary.commitment_id == commitment_id,
                CommitmentBeneficiary.status == "paid",
            )
            .count()
        )
        missed_cycles = (
            db.query(CommitmentBeneficiary)
            .filter(
                CommitmentBeneficiary.commitment_id == commitment_id,
                CommitmentBeneficiary.status == "missed",
            )
            .count()
        )
        snapshot = build_score_snapshot(
            base_score=12,
            contribution_history=contribution_points,
            missed_cycles=missed_cycles,
            completed_cycles=completed_cycles,
        )
        db.add(
            ScoreHistory(
                id=str(uuid.uuid4()),
                user_id=member.user_id,
                score=snapshot["score"],
                breakdown_json=serialize_score_snapshot(snapshot),
                computed_at=datetime.utcnow(),
            )
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
            if commitment.status == "completed":
                raise HTTPException(status_code=400, detail="Commitment is not accepting contributions.")

            member = (
                db.query(CommitmentMember)
                .filter(CommitmentMember.commitment_id == commitment_id, CommitmentMember.user_id == contributor_user_id)
                .one_or_none()
            )
            if member is None:
                raise HTTPException(status_code=400, detail="User is not a member of this commitment.")

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
                return response

            if payload.amount > commitment.contribution_amount:
                raise HTTPException(status_code=400, detail="Contribution amount cannot exceed the commitment amount.")

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
            if member_total_before >= commitment.contribution_amount:
                raise HTTPException(status_code=400, detail="This member has already completed the current cycle contribution.")
            if member_total_before + payload.amount > commitment.contribution_amount:
                raise HTTPException(status_code=400, detail="Contribution exceeds the member's remaining amount for this cycle.")
            cycle_total_before = (
                db.query(Contribution)
                .filter(
                    Contribution.commitment_id == commitment_id,
                    Contribution.cycle_number == current_cycle,
                )
                .with_entities(func.coalesce(func.sum(Contribution.amount), 0))
                .scalar()
            )

            db.add(
                Contribution(
                    id=str(uuid.uuid4()),
                    commitment_id=commitment_id,
                    cycle_number=current_cycle,
                    user_id=contributor_user_id,
                    amount=payload.amount,
                    event_id=payload.event_id,
                    status="full" if payload.amount == commitment.contribution_amount else "partial",
                    rule_trace_json="{}",
                    paid_at=datetime.utcnow(),
                )
            )
            db.flush()

            member_count = db.query(CommitmentMember).filter(CommitmentMember.commitment_id == commitment_id).count()
            contributions_for_cycle = (
                db.query(Contribution)
                .filter(Contribution.commitment_id == commitment_id, Contribution.cycle_number == current_cycle)
                .all()
            )
            distinct_contributors = len({row.user_id for row in contributions_for_cycle})
            member_total_after = member_total_before + payload.amount
            cycle_total_after = cycle_total_before + payload.amount
            evaluation = evaluate_contribution(
                contribution_amount=payload.amount,
                expected_member_amount=commitment.contribution_amount,
                member_total_before=member_total_before,
                cycle_total_before=cycle_total_before,
                member_count=member_count,
                distinct_contributors=distinct_contributors,
            )

            contribution_row = (
                db.query(Contribution)
                .filter(
                    Contribution.commitment_id == commitment_id,
                    Contribution.cycle_number == current_cycle,
                    Contribution.user_id == contributor_user_id,
                )
                .order_by(Contribution.paid_at.desc(), Contribution.id.desc())
                .first()
            )
            contribution_row.status = evaluation.contribution_status
            contribution_row.rule_trace_json = dump_rule_trace(evaluation)

            beneficiary_row = (
                db.query(CommitmentBeneficiary)
                .filter(
                    CommitmentBeneficiary.commitment_id == commitment_id,
                    CommitmentBeneficiary.cycle_number == current_cycle,
                )
                .one_or_none()
            )

            if evaluation.cycle_complete:
                if beneficiary_row is not None:
                    beneficiary_row.status = "paid"

                commitment.completed_cycle_count += 1
                if current_cycle >= commitment.cycles:
                    commitment.status = "completed"
                else:
                    commitment.current_cycle_number = current_cycle + 1
                    commitment.status = "active"
            elif evaluation.cycle_missed:
                if beneficiary_row is not None:
                    beneficiary_row.status = "missed"
                commitment.status = "missed"
            else:
                commitment.status = "active"

            _refresh_score_history_for_commitment(db, commitment_id)

            updated_commitment = db.get(Commitment, commitment_id)
            response = _serialize_commitment(updated_commitment, db)
            response.update(
                {
                    "status": updated_commitment.status,
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
            return response
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to record contribution.") from exc


def get_commitment_details(db: Session, commitment_id: str) -> dict[str, Any]:
    commitment = db.get(Commitment, commitment_id)
    if commitment is None:
        raise HTTPException(status_code=404, detail="Commitment not found.")
    return _serialize_commitment(commitment, db)


def redeem_cycle(db: Session, commitment_id: str, beneficiary_id: str) -> dict[str, Any]:
    with db.begin():
        commitment = db.get(Commitment, commitment_id)
        if commitment is None:
            raise HTTPException(status_code=404, detail="Commitment not found.")
        vendor = db.get(Vendor, commitment.vendor_id)
        if vendor is None or vendor.verified_at is None:
            raise HTTPException(status_code=400, detail="Commitment vendor is not verified.")
        beneficiary = (db.query(CommitmentBeneficiary)
            .filter(CommitmentBeneficiary.commitment_id == commitment_id,
                    CommitmentBeneficiary.user_id == beneficiary_id)
            .order_by(CommitmentBeneficiary.cycle_number.asc()).first())
        if beneficiary is None:
            raise HTTPException(status_code=403, detail="No cycle is available for this beneficiary.")
        existing = (db.query(Redemption)
            .filter(Redemption.commitment_id == commitment_id,
                    Redemption.cycle_number == beneficiary.cycle_number).one_or_none())
        if existing is not None:
            raise HTTPException(status_code=409, detail="This cycle has already been redeemed.")
        if beneficiary.status != "paid":
            raise HTTPException(status_code=400, detail="This beneficiary cycle is not ready for redemption.")
        voucher_code = f"SURA-{uuid.uuid4().hex[:10].upper()}"
        redemption = Redemption(id=str(uuid.uuid4()), commitment_id=commitment_id,
            beneficiary_id=beneficiary_id, vendor_id=commitment.vendor_id,
            cycle_number=beneficiary.cycle_number, amount=beneficiary.payout_amount,
            voucher_code=voucher_code, status="settled", redeemed_at=datetime.utcnow())
        db.add(redemption)
        beneficiary.status = "redeemed"
        return {"redemption_id": redemption.id, "commitment_id": commitment_id,
            "vendor_id": redemption.vendor_id, "cycle_number": redemption.cycle_number,
            "amount": redemption.amount, "voucher_code": voucher_code,
            "status": redemption.status, "redeemed_at": redemption.redeemed_at.isoformat()}
