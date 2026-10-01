"""Deterministic, advisory group-health signals for Sura Lock.

This is intentionally not a fraud engine, credit decision, or payment control.
It describes observed group-level Lock behaviour so a member or bank analyst can
understand whether a group needs attention. It never identifies a particular
member as risky and never changes commitment state.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Commitment, CommitmentBeneficiary, CommitmentMember, Contribution
from app.services.lock_lifecycle import deadline_state


def get_group_health(db: Session, commitment_id: str) -> dict[str, Any]:
    """Return an explainable group-level health assessment from persisted facts."""
    commitment = db.get(Commitment, commitment_id)
    if commitment is None:
        raise HTTPException(status_code=404, detail="Commitment not found.")
    if commitment.status == "cancelled":
        raise HTTPException(status_code=400, detail="Group health is unavailable for a cancelled commitment.")

    members = (
        db.query(CommitmentMember)
        .filter(CommitmentMember.commitment_id == commitment_id)
        .all()
    )
    joined_members = [member for member in members if member.role != "invited"]
    pending_invitation_count = len(members) - len(joined_members)
    beneficiaries = (
        db.query(CommitmentBeneficiary)
        .filter(CommitmentBeneficiary.commitment_id == commitment_id)
        .all()
    )
    completed_cycles = sum(item.status in {"paid", "redeemed"} for item in beneficiaries)
    missed_cycles = sum(item.status == "missed" for item in beneficiaries)

    current_cycle_contributions = (
        db.query(Contribution)
        .filter(
            Contribution.commitment_id == commitment_id,
            Contribution.cycle_number == commitment.current_cycle_number,
        )
        .all()
    )
    paid_by_member = {
        member.user_id: sum(
            contribution.amount
            for contribution in current_cycle_contributions
            if contribution.user_id == member.user_id
        )
        for member in joined_members
    }
    paid_member_count = sum(amount >= commitment.contribution_amount for amount in paid_by_member.values())
    partial_member_count = sum(0 < amount < commitment.contribution_amount for amount in paid_by_member.values())
    unpaid_member_count = sum(amount == 0 for amount in paid_by_member.values())
    required_current_total = commitment.contribution_amount * len(joined_members)
    contributed_current_total = sum(paid_by_member.values())
    current_deadline_state = deadline_state(
        due_at=commitment.current_cycle_due_at,
        grace_period_hours=commitment.grace_period_hours,
        now=datetime.utcnow(),
    )

    reasons: list[str] = []
    if missed_cycles:
        reasons.append(f"{missed_cycles} completed cycle(s) ended without the full pooled contribution.")
    if current_deadline_state == "overdue":
        reasons.append(
            "The current cycle is past its due date and within its agreed grace period."
        )
    elif current_deadline_state == "missed":
        reasons.append(
            "The current cycle is past its due date and grace period; lifecycle processing is required to persist a missed outcome."
        )
    if pending_invitation_count:
        reasons.append(f"{pending_invitation_count} invited member(s) have not joined, so group formation is incomplete.")
    if partial_member_count:
        reasons.append(f"{partial_member_count} joined member(s) have made a partial current-cycle contribution.")
    if commitment.status == "active" and unpaid_member_count:
        reasons.append(
            f"{unpaid_member_count} joined member(s) have not recorded a current-cycle contribution. "
            "The due date has not passed, so this is not labelled late."
        )
    if completed_cycles:
        reasons.append(f"{completed_cycles} cycle(s) have reached a paid or redeemed outcome.")
    if not reasons:
        reasons.append("The group has no adverse recorded Lock outcome yet.")

    if missed_cycles or current_deadline_state == "missed":
        group_health = "high_risk"
    elif current_deadline_state == "overdue" or pending_invitation_count or partial_member_count:
        group_health = "medium_risk"
    else:
        group_health = "low_risk"

    observed_closed_cycles = completed_cycles + missed_cycles
    confidence = "limited" if observed_closed_cycles == 0 else "moderate" if observed_closed_cycles < 3 else "strong"
    completion_rate = round(completed_cycles / observed_closed_cycles, 2) if observed_closed_cycles else None

    return {
        "commitment_id": commitment.id,
        "advisory": True,
        "group_health": group_health,
        "confidence": confidence,
        "reasons": reasons,
        "metrics": {
            "commitment_status": commitment.status,
            "member_count": len(members),
            "joined_member_count": len(joined_members),
            "pending_invitation_count": pending_invitation_count,
            "completed_cycles": completed_cycles,
            "missed_cycles": missed_cycles,
            "historical_cycle_completion_rate": completion_rate,
            "current_cycle_number": commitment.current_cycle_number,
            "current_cycle_due_at": (
                commitment.current_cycle_due_at.isoformat()
                if commitment.current_cycle_due_at
                else None
            ),
            "current_cycle_grace_period_hours": commitment.grace_period_hours,
            "current_cycle_deadline_state": current_deadline_state,
            "current_cycle_required_total": required_current_total,
            "current_cycle_contributed_total": contributed_current_total,
            "current_cycle_paid_member_count": paid_member_count,
            "current_cycle_partial_member_count": partial_member_count,
            "current_cycle_unpaid_member_count": unpaid_member_count,
        },
        "unavailable_signals": [
            "external payment-rail settlement",
            "member exit reason",
        ],
        "policy_note": "Advisory only. This result does not approve credit, block a contribution, or change payout order.",
    }


def get_group_health_for_member(db: Session, commitment_id: str, user_id: str) -> dict[str, Any]:
    """Scope the shared report to someone who belongs to the Lock."""
    member = (
        db.query(CommitmentMember)
        .filter(CommitmentMember.commitment_id == commitment_id, CommitmentMember.user_id == user_id)
        .one_or_none()
    )
    if member is None:
        raise HTTPException(status_code=403, detail="You are not a member of this commitment.")
    return get_group_health(db, commitment_id)
