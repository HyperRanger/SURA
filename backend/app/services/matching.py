"""Explainable vendor recommendations.

This is deliberately a deterministic advisory ranker. It never selects a
vendor for a member, enrols someone in a group, or changes a Lock. The inputs
are limited to facts Sura has recorded: verification, category, requested
payout amount, and completed in-Sura redemptions.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Redemption, Vendor


def _normalise_category(category: str | None) -> str | None:
    if category is None:
        return None
    normalised = category.strip().casefold()
    return normalised or None


def _amount_fit_points(target_amount: int | None, redemption_amounts: list[int]) -> tuple[int, str]:
    if target_amount is None:
        return 10, "No target payout amount was supplied, so amount fit is neutral."
    if not redemption_amounts:
        return 10, "No prior Sura redemption amount is available, so amount fit is neutral."

    typical_amount = sum(redemption_amounts) / len(redemption_amounts)
    difference_ratio = abs(target_amount - typical_amount) / max(target_amount, typical_amount)
    if difference_ratio <= 0.25:
        return 20, "The target payout is close to this vendor's prior Sura redemption amounts."
    if difference_ratio <= 0.50:
        return 14, "The target payout is within range of this vendor's prior Sura redemption amounts."
    return 6, "The target payout is outside this vendor's prior Sura redemption range."


def _history_points(redemptions: list[Redemption]) -> tuple[int, str]:
    if not redemptions:
        return 10, "This verified vendor has no prior Sura redemption history yet."

    settled_count = sum(redemption.status == "settled" for redemption in redemptions)
    if settled_count == len(redemptions):
        return 20, f"{settled_count} prior Sura redemption(s) completed successfully."
    return 8, f"{settled_count} of {len(redemptions)} prior Sura redemption(s) are settled."


def recommend_verified_vendors(
    db: Session,
    *,
    category: str | None = None,
    target_amount: int | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Rank verified vendors using a small, inspectable rule set.

    ``target_amount`` is the expected vendor redemption/payout amount, not an
    individual member's contribution. There is intentionally no location
    feature because the current Vendor model has no verified location data.
    """
    if target_amount is not None and target_amount <= 0:
        raise HTTPException(status_code=400, detail="target_amount must be positive.")
    if not 1 <= limit <= 20:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 20.")

    requested_category = _normalise_category(category)
    vendors = (
        db.query(Vendor)
        .filter(Vendor.verified_at.is_not(None))
        .order_by(Vendor.name.asc(), Vendor.id.asc())
        .all()
    )
    vendor_ids = [vendor.id for vendor in vendors]
    redemptions_by_vendor: dict[str, list[Redemption]] = defaultdict(list)
    if vendor_ids:
        for redemption in db.query(Redemption).filter(Redemption.vendor_id.in_(vendor_ids)).all():
            redemptions_by_vendor[redemption.vendor_id].append(redemption)

    recommendations: list[dict[str, Any]] = []
    for vendor in vendors:
        vendor_redemptions = redemptions_by_vendor[vendor.id]
        if requested_category is None:
            category_points = 15
            category_reason = "No category preference was supplied, so category fit is neutral."
        elif vendor.category.strip().casefold() == requested_category:
            category_points = 30
            category_reason = "The vendor category matches the requested category."
        else:
            category_points = 0
            category_reason = "The vendor category does not match the requested category."

        amount_points, amount_reason = _amount_fit_points(
            target_amount,
            [redemption.amount for redemption in vendor_redemptions],
        )
        history_points, history_reason = _history_points(vendor_redemptions)
        verification_points = 30
        score = verification_points + category_points + amount_points + history_points

        recommendations.append(
            {
                "vendor_id": vendor.id,
                "name": vendor.name,
                "category": vendor.category,
                "verified": True,
                "recommendation_score": score,
                "reasons": [
                    "The vendor is verified by Sura.",
                    category_reason,
                    amount_reason,
                    history_reason,
                ],
                "factor_points": {
                    "verification": verification_points,
                    "category_fit": category_points,
                    "amount_fit": amount_points,
                    "in_sura_redemption_history": history_points,
                },
            }
        )

    recommendations.sort(key=lambda item: (-item["recommendation_score"], item["name"].casefold(), item["vendor_id"]))
    return {
        "advisory": True,
        "requested_category": requested_category,
        "target_amount": target_amount,
        "recommendations": recommendations[:limit],
        "unavailable_signals": ["location", "external fulfilment history"],
        "group_recommendations_available": False,
        "group_recommendations_reason": (
            "Locks use private, pre-invited membership. Sura does not expose other groups for discovery or ranking."
        ),
    }
