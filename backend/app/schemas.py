from datetime import datetime
from typing import List, Literal, Optional

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


INDIVIDUAL_CONTEXTS = {"student", "trader", "freelancer", "other"}


class SignupRequest(BaseModel):
    """P2. The role is one of the two a person may pick for themselves; bank and
    admin accounts are provisioned and are rejected here."""

    role: Literal["individual", "vendor"]
    phone: str = Field(min_length=7, max_length=32)
    name: str = Field(min_length=1, max_length=200)

    context: Optional[Literal["student", "trader", "freelancer", "other"]] = None
    terms_accepted: bool = False

    business_name: Optional[str] = Field(default=None, max_length=200)
    business_category: Optional[str] = Field(default=None, max_length=120)
    business_phone: Optional[str] = Field(default=None, max_length=32)


class LoginRequest(BaseModel):
    """P3."""

    phone: str = Field(min_length=7, max_length=32)


class VerifyOtpRequest(BaseModel):
    """P4."""

    challenge_id: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=4, max_length=12)


class DemoLoginAsRequest(BaseModel):
    """P8. Non-production only."""

    role: Literal["individual", "vendor", "bank"] = "individual"


class BankLoginRequest(BaseModel):
    """B1. Email and password for a provisioned Bank Portal staff account."""

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class BankVerifyMfaRequest(BaseModel):
    """B1. Second factor issued by the bank login step."""

    challenge_id: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=4, max_length=12)


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
