from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    institution_id: Mapped[str | None] = mapped_column(String, ForeignKey("institutions.id"), nullable=True)
    phone: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    bank_customer_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    bank_id: Mapped[str | None] = mapped_column(String, ForeignKey("bank_partners.id"), nullable=True, index=True)

    # Assigned by the backend at signup and carried in the token. The frontend
    # route is never trusted for this; every protected endpoint reads the claim.
    role: Mapped[str] = mapped_column(String, nullable=False, default="individual")
    # Set when role is vendor, so the account resolves to one exact vendor
    # record rather than guessing by business name.
    vendor_id: Mapped[str | None] = mapped_column(String, ForeignKey("vendors.id"), nullable=True)
    # Student / trader / freelancer / other. Personalises onboarding only, and
    # grants no extra permission.
    context: Mapped[str | None] = mapped_column(String, nullable=True)
    terms_accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    phone_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Set by a bank's risk analyst, never by the member. ``active`` is the only
    # state that permits money to move; ``restricted`` blocks new contributions
    # and voucher redemption while leaving read access intact, so a member can
    # still see why they cannot transact. ``suspended`` additionally refuses
    # sign-in. The reason is required whenever a state is not ``active`` because
    # the decision is shown back to the member and audited.
    account_status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    restriction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    restricted_by: Mapped[str | None] = mapped_column(String, nullable=True)
    restricted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Raised by "sign out everywhere". A token issued before this instant is
    # refused on sight, which is how every outstanding session ends at once
    # without the service having to keep a table of live tokens.
    session_invalidated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ContactLookupRateLimit(Base):
    """One rolling fixed-window counter per authenticated contact resolver.

    It deliberately stores no searched phone number. The only data required to
    throttle account discovery is the caller identity, the current window, and
    the attempt count.
    """

    __tablename__ = "contact_lookup_rate_limits"

    requester_user_id: Mapped[str] = mapped_column(String, primary_key=True)
    window_started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class PlatformAuditEvent(Base):
    """A record of who did what across the whole platform.

    ``bank_audit_events`` answers the same question inside one institution, which
    is what a bank's own compliance review needs. It cannot answer the questions
    a platform operator asks: was this credential reset by someone at the same
    bank or outside it, which sign-ins failed across all tenants, did one analyst
    account touch accounts at several institutions. ``institution_id`` is
    therefore nullable, and a row with no institution is a platform-level event
    rather than an orphaned one.

    Append-only by construction: nothing in the codebase updates or deletes these
    rows.
    """

    __tablename__ = "platform_audit_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String, nullable=True)
    institution_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # What the event happened to: user, bank_staff, api_key, session, and so on.
    subject_type: Mapped[str] = mapped_column(String, nullable=False)
    subject_id: Mapped[str] = mapped_column(String, nullable=False)
    # Free-form context, and explicitly not a place for credentials: callers pass
    # identifiers and outcomes, never the secret being changed.
    detail_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    # The caller's IP and user agent, when a request supplied them. Nullable,
    # because background jobs have neither.
    source_ip: Mapped[str | None] = mapped_column(String, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class SessionRevocation(Base):
    """A signed-out session, recorded so the token stops working immediately.

    A JWT is valid until it expires. Without a row here, "log out" would only
    clear the token client-side and a copied or stolen token would keep working
    for the rest of its 24-hour life. Storing the token's own identifier, rather
    than the token, means a leaked database cannot be replayed as a login: the
    stored value is a hash.
    """

    __tablename__ = "session_revocations"

    jti: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String, nullable=False, default="logout")
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class AuthChallenge(Base):
    """A pending one-time code for signup or login.

    Only a salted hash of the code is stored, and a challenge is consumed on
    first successful use, so a leaked database row cannot be replayed as a login.
    """

    __tablename__ = "auth_challenges"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String, nullable=False)
    code_hash: Mapped[str] = mapped_column(String, nullable=False)
    salt: Mapped[str] = mapped_column(String, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    fee_calendar_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Commitment(Base):
    __tablename__ = "commitments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    creator_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False, default="rotating")
    title: Mapped[str] = mapped_column(String, nullable=False)
    vendor_id: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), nullable=False)
    contribution_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    frequency: Mapped[str] = mapped_column(String, nullable=False)
    cycles: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending_members")
    invite_code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    payout_order_json: Mapped[str] = mapped_column(Text, nullable=False)
    current_cycle_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    completed_cycle_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Deadlines are stored rather than inferred at read time, so a frequency
    # change or a later code release cannot rewrite the group agreement.
    first_cycle_due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_cycle_due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    grace_period_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=72)
    missed_cycle_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


class CommitmentMember(Base):
    __tablename__ = "commitment_members"

    commitment_id: Mapped[str] = mapped_column(String, ForeignKey("commitments.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String, nullable=False, default="contributor")
    joined_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    declined_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CommitmentBeneficiary(Base):
    __tablename__ = "commitment_beneficiaries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    commitment_id: Mapped[str] = mapped_column(String, ForeignKey("commitments.id"), nullable=False)
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    payout_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="scheduled")


class Contribution(Base):
    __tablename__ = "contributions"
    __table_args__ = (
        UniqueConstraint("commitment_id", "user_id", "event_id", name="uq_contributions_commitment_user_event"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    commitment_id: Mapped[str] = mapped_column(String, ForeignKey("commitments.id"), nullable=False)
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    event_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="full")
    rule_trace_json: Mapped[str] = mapped_column(Text, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


class Redemption(Base):
    __tablename__ = "redemptions"
    __table_args__ = (
        UniqueConstraint("commitment_id", "cycle_number", name="uq_redemptions_commitment_cycle"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    commitment_id: Mapped[str] = mapped_column(String, ForeignKey("commitments.id"), nullable=False)
    beneficiary_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    vendor_id: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), nullable=False)
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    voucher_code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="settled")
    redeemed_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


class ScoreHistory(Base):
    __tablename__ = "score_history"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    breakdown_json: Mapped[str] = mapped_column(Text, nullable=False)
    computed_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    score_before: Mapped[int | None] = mapped_column(Integer, nullable=True)
    event_type: Mapped[str | None] = mapped_column(String, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    signals_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    score_version: Mapped[str | None] = mapped_column(String, nullable=True)
    bank_id: Mapped[str | None] = mapped_column(String, ForeignKey("bank_partners.id"), nullable=True, index=True)


class AccountActivitySignal(Base):
    __tablename__ = "account_activity_signals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)
    institution_id: Mapped[str | None] = mapped_column(String, ForeignKey("institutions.id"), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class UserConsent(Base):
    __tablename__ = "user_consents"
    __table_args__ = (
        UniqueConstraint("user_id", "consent_type", name="uq_user_consents_user_type"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    consent_type: Mapped[str] = mapped_column(String, nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    recorded_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


class CommitmentActivity(Base):
    __tablename__ = "commitment_activities"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    commitment_id: Mapped[str] = mapped_column(String, ForeignKey("commitments.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    cycle_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


class Voucher(Base):
    __tablename__ = "vouchers"
    __table_args__ = (
        UniqueConstraint("commitment_id", "cycle_number", name="uq_vouchers_commitment_cycle"),
    )

    __table_args__ = (
        UniqueConstraint("commitment_id", "cycle_number", name="uq_vouchers_commitment_cycle"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    commitment_id: Mapped[str] = mapped_column(String, ForeignKey("commitments.id"), nullable=False)
    beneficiary_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    vendor_id: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), nullable=False)
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ready")
    issued_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    redeemed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CommitmentCase(Base):
    """A bank-operated hold for a disputed Lock; it never alters money terms."""

    __tablename__ = "commitment_cases"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    commitment_id: Mapped[str] = mapped_column(String, ForeignKey("commitments.id"), nullable=False, index=True)
    bank_id: Mapped[str] = mapped_column(String, ForeignKey("bank_partners.id"), nullable=False, index=True)
    opened_by: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="open")
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


