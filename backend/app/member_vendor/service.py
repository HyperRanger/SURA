"""Read models for the member/vendor PWA.

These functions deliberately compose established domain services. They do not
reimplement commitment, score, or voucher rules.
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import Vendor
from app.services import auth_service
from app.services.commitments import list_member_commitments, list_vendor_redemptions
from app.services.score_service import public_score_report


def get_member_home(db: Session, user_id: str) -> dict[str, Any]:
    commitments = list_member_commitments(db, user_id)
    next_payout: dict[str, Any] | None = None

    for commitment in commitments:
        if commitment["status"] not in {"active", "pending_members"}:
            continue
        current_cycle = commitment["current_cycle_number"]
        cycle = next(
            (item for item in commitment["cycle_states"] if item["cycle_number"] == current_cycle),
            None,
        )
        if cycle is not None:
            next_payout = {
                "commitment_id": commitment["commitment_id"],
                "title": commitment["title"],
                **cycle,
            }
            break

    # Match the dedicated Score endpoint exactly. The PWA should not need to
    # account for internal snapshot fields appearing only after a score change.
    score = public_score_report(db, user_id)
    return {
        "profile": auth_service.get_profile(db, user_id),
        "score": score,
        "commitments": commitments,
        "active_commitment_count": sum(item["status"] == "active" for item in commitments),
        "next_payout": next_payout,
    }


def get_vendor_overview(db: Session, vendor_id: str) -> dict[str, Any]:
    redemptions = list_vendor_redemptions(db, vendor_id)
    vendor = db.get(Vendor, vendor_id)
    today = date.today()
    today_rows = [
        item
        for item in redemptions
        if item["redeemed_at"] and datetime.fromisoformat(item["redeemed_at"]).date() == today
    ]
    return {
        "vendor_id": vendor_id,
        "merchant": (
            {
                "vendor_id": vendor.id,
                "name": vendor.name,
                "category": vendor.category,
                "verified": vendor.verified_at is not None,
            }
            if vendor is not None
            else None
        ),
        "today_settled_amount": sum(item["amount"] for item in today_rows),
        "today_redemption_count": len(today_rows),
        "recent_redemptions": redemptions[:10],
    }
