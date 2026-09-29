from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    institution_id = Column(String, ForeignKey("institutions.id"), nullable=True)
    phone = Column(String, nullable=False, unique=True)
    verified_at = Column(DateTime, nullable=True)
    bank_customer_id = Column(String, nullable=True, index=True)
    bank_id = Column(String, ForeignKey("bank_partners.id"), nullable=True, index=True)

    # Assigned by the backend at signup and carried in the token. The frontend
    # route is never trusted for this; every protected endpoint reads the claim.
    role = Column(String, nullable=False, default="individual")
    # Set when role is vendor, so the account resolves to one exact vendor
    # record rather than guessing by business name.
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=True)
    # Student / trader / freelancer / other. Personalises onboarding only, and
    # grants no extra permission.
    context = Column(String, nullable=True)
    terms_accepted_at = Column(DateTime, nullable=True)
    phone_verified_at = Column(DateTime, nullable=True)


class AuthChallenge(Base):
    """A pending one-time code for signup or login.

    Only a salted hash of the code is stored, and a challenge is consumed on
    first successful use, so a leaked database row cannot be replayed as a login.
    """

    __tablename__ = "auth_challenges"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    purpose = Column(String, nullable=False)
    code_hash = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    consumed_at = Column(DateTime, nullable=True)


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    fee_calendar_json = Column(Text, nullable=True)


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    verified_at = Column(DateTime, nullable=True)


class Commitment(Base):
    __tablename__ = "commitments"

    id = Column(String, primary_key=True)
    creator_id = Column(String, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False, default="rotating")
    title = Column(String, nullable=False)
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=False)
    contribution_amount = Column(Integer, nullable=False)
    frequency = Column(String, nullable=False)
    cycles = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="pending_members")
    invite_code = Column(String, nullable=False, unique=True)
    payout_order_json = Column(Text, nullable=False)
    current_cycle_number = Column(Integer, nullable=False, default=1)
    completed_cycle_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class CommitmentMember(Base):
    __tablename__ = "commitment_members"

    commitment_id = Column(String, ForeignKey("commitments.id"), primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    role = Column(String, nullable=False, default="contributor")
    joined_at = Column(DateTime, default=datetime.utcnow)


class CommitmentBeneficiary(Base):
    __tablename__ = "commitment_beneficiaries"

    id = Column(String, primary_key=True)
    commitment_id = Column(String, ForeignKey("commitments.id"), nullable=False)
    cycle_number = Column(Integer, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    payout_amount = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="scheduled")


class Contribution(Base):
    __tablename__ = "contributions"
    __table_args__ = (
        UniqueConstraint("commitment_id", "user_id", "event_id", name="uq_contributions_commitment_user_event"),
    )

    id = Column(String, primary_key=True)
    commitment_id = Column(String, ForeignKey("commitments.id"), nullable=False)
    cycle_number = Column(Integer, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    event_id = Column(String, nullable=False)
    status = Column(String, nullable=False, default="full")
    rule_trace_json = Column(Text, nullable=False)
    paid_at = Column(DateTime, default=datetime.utcnow)


class Redemption(Base):
    __tablename__ = "redemptions"
    __table_args__ = (
        UniqueConstraint("commitment_id", "cycle_number", name="uq_redemptions_commitment_cycle"),
    )

    id = Column(String, primary_key=True)
    commitment_id = Column(String, ForeignKey("commitments.id"), nullable=False)
    beneficiary_id = Column(String, ForeignKey("users.id"), nullable=False)
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=False)
    cycle_number = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)
    voucher_code = Column(String, nullable=False, unique=True)
    status = Column(String, nullable=False, default="settled")
    redeemed_at = Column(DateTime, default=datetime.utcnow)


class ScoreHistory(Base):
    __tablename__ = "score_history"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    breakdown_json = Column(Text, nullable=False)
    computed_at = Column(DateTime, default=datetime.utcnow)
    score_before = Column(Integer, nullable=True)
    event_type = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    source_id = Column(String, nullable=True)
    signals_json = Column(Text, nullable=True)
    score_version = Column(String, nullable=True)


class AccountActivitySignal(Base):
    __tablename__ = "account_activity_signals"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    institution_id = Column(String, ForeignKey("institutions.id"), nullable=True, index=True)
    source = Column(String, nullable=False)
    occurred_at = Column(DateTime, nullable=False)


class UserConsent(Base):
    __tablename__ = "user_consents"
    __table_args__ = (
        UniqueConstraint("user_id", "consent_type", name="uq_user_consents_user_type"),
    )

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    consent_type = Column(String, nullable=False)
    granted = Column(Boolean, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)


class CommitmentActivity(Base):
    __tablename__ = "commitment_activities"

    id = Column(String, primary_key=True)
    commitment_id = Column(String, ForeignKey("commitments.id"), nullable=False)
    event_type = Column(String, nullable=False)
    actor_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    cycle_number = Column(Integer, nullable=True)
    detail_json = Column(Text, nullable=False, default="{}")
    occurred_at = Column(DateTime, default=datetime.utcnow)


class Voucher(Base):
    __tablename__ = "vouchers"
    __table_args__ = (
        UniqueConstraint("commitment_id", "cycle_number", name="uq_vouchers_commitment_cycle"),
    )

    id = Column(String, primary_key=True)
    commitment_id = Column(String, ForeignKey("commitments.id"), nullable=False)
    beneficiary_id = Column(String, ForeignKey("users.id"), nullable=False)
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=False)
    cycle_number = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)
    code = Column(String, nullable=False, unique=True)
    status = Column(String, nullable=False, default="ready")
    issued_at = Column(DateTime, default=datetime.utcnow)
    redeemed_at = Column(DateTime, nullable=True)
