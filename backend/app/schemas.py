from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class LockRequest(BaseModel):
    type: str = "rotating"
    title: str
    vendor_id: str
    contribution_amount: int
    contribution_frequency: str
    cycles: int
    members: List[str]
    payout_order: Optional[List[str]] = None
    creator_id: Optional[str] = None


class ContributionRequest(BaseModel):
    amount: int
    event_id: str = Field(min_length=1, max_length=128, description="Stable client ID reused for retries of this contribution.")


class DemoTokenRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    otp_code: str = Field(min_length=1, max_length=32)


class VendorVerificationRequest(BaseModel):
    vendor_id: str
    name: Optional[str] = None
    category: Optional[str] = None


class ConsentRequest(BaseModel):
    granted: bool


class JoinCommitmentRequest(BaseModel):
    invite_code: str = Field(min_length=1, max_length=64)


class VendorRedeemRequest(BaseModel):
    voucher_code: str = Field(min_length=1, max_length=64)


class PayoutScheduleItem(BaseModel):
    cycle: int
    beneficiary_id: str
    amount: int


class LockResponse(BaseModel):
    commitment_id: str
    type: str
    status: str
    invite_code: str
    payout_schedule: List[PayoutScheduleItem]


class ScoreBreakdown(BaseModel):
    commitment_behaviour: int
    repayment_behaviour: int
    transaction_stability: int
    institutional_verification: int
    social_reliability: int


class ScoreResponse(BaseModel):
    user_id: str
    score: int
    tier: str
    breakdown: ScoreBreakdown
    weights: dict[str, float]
    score_version: str
    last_updated: datetime


class ScoreHistoryEntry(BaseModel):
    score: int
    score_before: Optional[int] = None
    event_type: Optional[str] = None
    source_id: Optional[str] = None
    reason: Optional[str] = None
    computed_at: datetime
    breakdown: Optional[ScoreBreakdown] = None


class ScoreHistoryResponse(BaseModel):
    user_id: str
    current_score: int
    entries: List[ScoreHistoryEntry]
