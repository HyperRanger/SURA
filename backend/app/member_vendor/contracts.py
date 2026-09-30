"""Stable response contracts owned by the member/vendor PWA."""

from typing import Any

from pydantic import BaseModel


class MemberHomeResponse(BaseModel):
    """Data for the member home screen; no other member's score is included."""

    profile: dict[str, Any]
    score: dict[str, Any]
    commitments: list[dict[str, Any]]
    active_commitment_count: int
    next_payout: dict[str, Any] | None


class VendorOverviewResponse(BaseModel):
    """Minimal, merchant-scoped data for the vendor terminal landing screen."""

    vendor_id: str
    today_settled_amount: int
    today_redemption_count: int
    recent_redemptions: list[dict[str, Any]]
