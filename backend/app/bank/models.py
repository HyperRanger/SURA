"""Database records owned exclusively by the Bank Portal domain."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

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


class BankStaff(Base):
    """A person who signs in to the Bank Portal with an email and password.

    Deliberately not a role on ``users``. Signup authenticates by phone and
    assigns its own role, so a bank login stored there would either be
    unreachable or reachable by the wrong flow. Keeping credentials, the role and
    the permission set in one row owned by the bank domain also means a staff
    account is revoked by changing this table, not by editing a customer row.
    """

    __tablename__ = "bank_staff"

    id = Column(String, primary_key=True)
    bank_id = Column(String, ForeignKey("bank_partners.id"), nullable=False, index=True)
    # A staff member is still a user record, so the session subject, the audit
    # actor and the profile endpoints all resolve the same way as any other login.
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    permissions_json = Column(Text, nullable=False, default="[]")
    # Where the second factor is sent. Null means this account has no second
    # factor available, which the login flow refuses rather than silently skipping.
    mfa_phone = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active")
    failed_password_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BankApiKey(Base):
    __tablename__ = "bank_api_keys"

    id = Column(String, primary_key=True)
    bank_id = Column(String, ForeignKey("bank_partners.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    key_prefix = Column(String, nullable=False)
    secret_hash = Column(String, nullable=False)
    scopes_json = Column(Text, nullable=False, default="[]")
    environment = Column(String, nullable=False, default="sandbox")
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"

    id = Column(String, primary_key=True)
    bank_id = Column(String, ForeignKey("bank_partners.id"), nullable=False, index=True)
    url = Column(String, nullable=False)
    event_types_json = Column(Text, nullable=False, default="[]")
    status = Column(String, nullable=False, default="active")
    signing_secret_hash = Column(String, nullable=False)
    signing_secret_encrypted = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(String, primary_key=True)
    webhook_id = Column(String, ForeignKey("webhook_subscriptions.id"), nullable=False, index=True)
    bank_id = Column(String, ForeignKey("bank_partners.id"), nullable=False, index=True)
    event_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    payload_json = Column(Text, nullable=False)
    signature = Column(String, nullable=False)
    attempt_number = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False, default="queued")
    response_status = Column(Integer, nullable=True)
    response_summary = Column(Text, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
