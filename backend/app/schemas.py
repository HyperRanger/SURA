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


class VendorVerificationRequest(BaseModel):
    vendor_id: str
    name: Optional[str] = None
    category: Optional[str] = None


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
    commitment_behaviour: float
    repayment_behaviour: float
    transaction_stability: float
    institutional_verification: float
    social_reliability: float


class ScoreResponse(BaseModel):
    user_id: str
    score: int
    breakdown: ScoreBreakdown
    last_updated: datetime
