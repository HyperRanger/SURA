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
    merchant: dict[str, Any] | None
    today_settled_amount: int
    today_redemption_count: int
    recent_redemptions: list[dict[str, Any]]


class VendorRecommendationsResponse(BaseModel):
    """An advisory vendor ranking; it is never an automatic selection."""

    advisory: bool
    requested_category: str | None
    target_amount: int | None
    recommendations: list[dict[str, Any]]
    unavailable_signals: list[str]
    group_recommendations_available: bool
    group_recommendations_reason: str


class GroupHealthResponse(BaseModel):
    """Group-level Lock health; never an individual fraud or credit decision."""

    commitment_id: str
    advisory: bool
    group_health: str
    confidence: str
    reasons: list[str]
    metrics: dict[str, Any]
    unavailable_signals: list[str]
    policy_note: str
