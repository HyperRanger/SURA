"""Database records owned exclusively by the Bank Portal domain."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.database import Base


class BankPartner(Base):
    __tablename__ = "bank_partners"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class RiskFlag(Base):
    __tablename__ = "risk_flags"

    id = Column(String, primary_key=True)
    bank_id = Column(String, ForeignKey("bank_partners.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    rule = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    status = Column(String, nullable=False, default="open")
    evidence_json = Column(Text, nullable=False, default="{}")
    resolution_note = Column(Text, nullable=True)
    resolved_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class BankAuditEvent(Base):
    __tablename__ = "bank_audit_events"

    id = Column(String, primary_key=True)
    bank_id = Column(String, ForeignKey("bank_partners.id"), nullable=False, index=True)
    actor_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    subject_type = Column(String, nullable=False)
    subject_id = Column(String, nullable=False)
    detail_json = Column(Text, nullable=False, default="{}")
    occurred_at = Column(DateTime, default=datetime.utcnow)
