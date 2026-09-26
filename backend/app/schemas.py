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


class ContributionRequest(BaseModel):
    user_id: str
    amount: int


class VendorVerificationRequest(BaseModel):
    vendor_id: str
    verified: bool = True


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
