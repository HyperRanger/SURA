"""Database records owned exclusively by the Bank Portal domain."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BankPartner(Base):
    __tablename__ = "bank_partners"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    environment: Mapped[str] = mapped_column(String, nullable=False, default="sandbox")
    supported_vendor_categories_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=365)
    security_settings_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


class RiskFlag(Base):
    __tablename__ = "risk_flags"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    bank_id: Mapped[str] = mapped_column(String, ForeignKey("bank_partners.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)
    rule: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="open")
    evidence_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AccountRestriction(Base):
    """One decision to limit or suspend a member, kept as its own record.

    ``users.account_status`` holds only the current state so that authorisation is
    a single column read on every money-moving request. This table answers the
    question a regulator asks: who restricted this member, when, on what evidence,
    and who lifted it. Both are required, because a bare status column cannot
    reconstruct a decision trail.
    """

    __tablename__ = "account_restrictions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    bank_id: Mapped[str] = mapped_column(String, ForeignKey("bank_partners.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    flag_id: Mapped[str | None] = mapped_column(String, ForeignKey("risk_flags.id"), nullable=True)
    actor_id: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    lifted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    lifted_by: Mapped[str | None] = mapped_column(String, nullable=True)


class BankAuditEvent(Base):
    __tablename__ = "bank_audit_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    bank_id: Mapped[str] = mapped_column(String, ForeignKey("bank_partners.id"), nullable=False, index=True)
    actor_id: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    subject_type: Mapped[str] = mapped_column(String, nullable=False)
    subject_id: Mapped[str] = mapped_column(String, nullable=False)
    detail_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


class BankStaff(Base):
    """A person who signs in to the Bank Portal with an email and password.

    Deliberately not a role on ``users``. Signup authenticates by phone and
    assigns its own role, so a bank login stored there would either be
    unreachable or reachable by the wrong flow. Keeping credentials, the role and
    the permission set in one row owned by the bank domain also means a staff
    account is revoked by changing this table, not by editing a customer row.
    """

    __tablename__ = "bank_staff"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    bank_id: Mapped[str] = mapped_column(String, ForeignKey("bank_partners.id"), nullable=False, index=True)
    # A staff member is still a user record, so the session subject, the audit
    # actor and the profile endpoints all resolve the same way as any other login.
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    permissions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # Where the second factor is sent. Null means this account has no second
    # factor available, which the login flow refuses rather than silently skipping.
    mfa_phone: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    failed_password_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


class BankApiKey(Base):
    __tablename__ = "bank_api_keys"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    bank_id: Mapped[str] = mapped_column(String, ForeignKey("bank_partners.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    key_prefix: Mapped[str] = mapped_column(String, nullable=False)
    secret_hash: Mapped[str] = mapped_column(String, nullable=False)
    scopes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    environment: Mapped[str] = mapped_column(String, nullable=False, default="sandbox")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    bank_id: Mapped[str] = mapped_column(String, ForeignKey("bank_partners.id"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    event_types_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    signing_secret_hash: Mapped[str] = mapped_column(String, nullable=False)
    signing_secret_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    webhook_id: Mapped[str] = mapped_column(String, ForeignKey("webhook_subscriptions.id"), nullable=False, index=True)
    bank_id: Mapped[str] = mapped_column(String, ForeignKey("bank_partners.id"), nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    signature: Mapped[str] = mapped_column(String, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String, nullable=False, default="queued")
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
