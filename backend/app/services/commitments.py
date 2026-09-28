import json
import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    Commitment,
    CommitmentActivity,
    CommitmentBeneficiary,
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
from app.services.payout_rules import apply_anchor_and_cap_rule, build_payout_schedule
from app.services.scoring import build_score_snapshot, serialize_score_snapshot

ENTRY_TIER_SCORE = 12


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
    return member


def _activate_if_fully_joined(db: Session, commitment: Commitment) -> None:
    db.flush()
    invited_count = (
        db.query(CommitmentMember)
        .filter(CommitmentMember.commitment_id == commitment.id, CommitmentMember.role == "invited")
        .count()
    )
    if invited_count == 0 and commitment.status == "pending_members":
        commitment.status = "active"


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
    vouchers = (
        db.query(Voucher)
        .filter(Voucher.commitment_id == commitment.id)
        .order_by(Voucher.cycle_number.asc())
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
        "vouchers": [_serialize_voucher_state(voucher) for voucher in vouchers],
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
                details={"title": commitment.title, "vendor_id": commitment.vendor_id, "member_count": len(member_ids)},
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
    reason: str = "contribution_processed",
) -> None:
    commitment = db.get(Commitment, commitment_id)
    if commitment is None:
        return

    members = (
        db.query(CommitmentMember)
        .filter(CommitmentMember.commitment_id == commitment_id)
        .all()
    )
    # Sessions run with autoflush=False, so the beneficiary status the caller
    # just set is still only in memory. Without this flush the paid/missed
    # counts below read the database as it was before this contribution and
    # silently drop the cycle-completion bonus from the score.
    db.flush()

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
        previous = (
            db.query(ScoreHistory)
            .filter(ScoreHistory.user_id == member.user_id)
            .order_by(ScoreHistory.computed_at.desc(), ScoreHistory.id.desc())
            .first()
        )
        previous_score = previous.score if previous is not None else None
        if previous_score == snapshot["score"]:
            # This member's score did not move, so there is no change to
            # explain. Recording a row here would attribute someone else's
            # contribution to them and pad the audit trail with no-ops.
            continue
        db.add(
            ScoreHistory(
                id=str(uuid.uuid4()),
                user_id=member.user_id,
                score=snapshot["score"],
                old_score=previous_score,
                event_id=event_id,
                reason=reason,
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
            member = _require_member(db, commitment_id, contributor_user_id)
            if member.role == "invited":
                raise HTTPException(status_code=400, detail="Join this commitment before contributing.")

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

            if commitment.status != "active":
                raise HTTPException(status_code=400, detail="Commitment is not accepting contributions.")

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
                if beneficiary_row is not None:
                    beneficiary_row.status = "paid"
                    _record_activity(
                        db,
                        commitment_id,
                        "cycle_paid",
                        cycle_number=current_cycle,
                        details={"beneficiary_id": beneficiary_row.user_id, "amount": beneficiary_row.payout_amount},
                    )
                    _issue_voucher_if_needed(db, commitment, beneficiary_row)

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

            _refresh_score_history_for_commitment(
                db,
                commitment_id,
                event_id=payload.event_id,
                reason="contribution_processed",
            )

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


def get_commitment_details(db: Session, commitment_id: str, requester_user_id: str) -> dict[str, Any]:
    commitment = db.get(Commitment, commitment_id)
    if commitment is None:
        raise HTTPException(status_code=404, detail="Commitment not found.")
    _require_member(db, commitment_id, requester_user_id)
    return _serialize_commitment(commitment, db)


def list_member_commitments(db: Session, user_id: str) -> list[dict[str, Any]]:
    commitments = (
        db.query(Commitment)
        .join(CommitmentMember, CommitmentMember.commitment_id == Commitment.id)
        .filter(CommitmentMember.user_id == user_id)
        .order_by(Commitment.created_at.desc(), Commitment.id.desc())
        .all()
    )
    return [_serialize_commitment(commitment, db) for commitment in commitments]


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
        voucher = (
            db.query(Voucher)
            .filter(Voucher.commitment_id == commitment_id, Voucher.cycle_number == cycle_number)
            .one_or_none()
        )
        if voucher is not None:
            return _serialize_voucher(voucher)
        if beneficiary.status == "paid":
            voucher = _issue_voucher_if_needed(db, commitment, beneficiary)
            db.flush()
            return _serialize_voucher(voucher)
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
                    "cycle_number": cycle_number,
                    "amount": redemption.amount,
                    "voucher_code": redemption.voucher_code,
                    "status": "redeemed",
                    "issued_at": None,
                    "redeemed_at": redemption.redeemed_at.isoformat() if redemption.redeemed_at else None,
                }
        return {
            "commitment_id": commitment_id,
            "beneficiary_id": beneficiary.user_id,
            "vendor_id": commitment.vendor_id,
            "cycle_number": cycle_number,
            "amount": beneficiary.payout_amount,
            "voucher_code": None,
            "status": "locked",
            "issued_at": None,
            "redeemed_at": None,
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
    return {
        "voucher": _serialize_voucher(voucher),
        "commitment_title": commitment.title if commitment else None,
        "beneficiary_id": voucher.beneficiary_id,
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
            details={"vendor_id": vendor_id, "amount": voucher.amount, "voucher_code": voucher.code},
        )
        return {
            "redemption_id": redemption.id,
            "commitment_id": voucher.commitment_id,
            "vendor_id": redemption.vendor_id,
            "cycle_number": redemption.cycle_number,
            "amount": redemption.amount,
            "voucher_code": voucher.code,
            "status": redemption.status,
            "redeemed_at": redemption.redeemed_at.isoformat(),
        }


def list_vendor_redemptions(db: Session, vendor_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(Redemption)
        .filter(Redemption.vendor_id == vendor_id)
        .order_by(Redemption.redeemed_at.desc(), Redemption.id.desc())
        .all()
    )
    return [
        {
            "redemption_id": redemption.id,
            "commitment_id": redemption.commitment_id,
            "beneficiary_id": redemption.beneficiary_id,
            "cycle_number": redemption.cycle_number,
            "amount": redemption.amount,
            "voucher_code": redemption.voucher_code,
            "status": redemption.status,
            "redeemed_at": redemption.redeemed_at.isoformat() if redemption.redeemed_at else None,
        }
        for redemption in rows
    ]
