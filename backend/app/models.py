from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    institution_id = Column(String, ForeignKey("institutions.id"), nullable=True)
    phone = Column(String, nullable=False, unique=True)
    verified_at = Column(DateTime, nullable=True)


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

    id = Column(String, primary_key=True)
    commitment_id = Column(String, ForeignKey("commitments.id"), nullable=False)
    cycle_number = Column(Integer, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="full")
    rule_trace_json = Column(Text, nullable=False)
    paid_at = Column(DateTime, default=datetime.utcnow)


class ScoreHistory(Base):
    __tablename__ = "score_history"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    breakdown_json = Column(Text, nullable=False)
    computed_at = Column(DateTime, default=datetime.utcnow)
