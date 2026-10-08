"""Platform-wide audit trail.

One append-only record of consequential actions, spanning every tenant. Distinct
from ``bank_audit_events``, which stays inside one institution because that is
the boundary a bank's own compliance review works at.

Two rules make the trail worth keeping:

A failed action is recorded as well as a successful one. A trail that only shows
successes cannot answer "who tried", which is usually the question that matters.

No secret is ever passed in. Callers pass identifiers and outcomes. The
``detail_json`` is built from whatever the caller chose to include, so the
convention is that callers pass state changes, never the credential behind one.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import PlatformAuditEvent

logger = logging.getLogger(__name__)


# Action vocabulary. Constrained to a closed set so a typo cannot silently create
# an event type nobody queries, and so the set can be reviewed as a whole.
LOGIN_SUCCEEDED = "auth.login.succeeded"
LOGIN_MFA_CHALLENGED = "auth.login.mfa_challenged"
LOGIN_FAILED = "auth.login.failed"
LOGOUT = "auth.logout"
LOGOUT_ALL = "auth.logout_all"
SESSION_REVOKED_BY_STAFF = "auth.session.revoked_by_staff"
PASSWORD_CHANGED = "auth.password.changed"
PASSWORD_RESET = "auth.password.reset"
ACCOUNT_LOCKED = "auth.account.locked"

STAFF_PROVISIONED = "staff.provisioned"
STAFF_UPDATED = "staff.updated"
STAFF_PERMISSIONS_CHANGED = "staff.permissions.changed"

RISK_RULES_RUN = "risk.rules_run"
FLAG_CREATED = "risk.flag_created"
FLAG_RESOLVED = "risk.flag_resolved"
ACCOUNT_RESTRICTED = "risk.account_restricted"
ACCOUNT_REINSTATED = "risk.account_reinstated"

KNOWN_EVENT_TYPES = frozenset(
    {
        LOGIN_SUCCEEDED,
        LOGIN_MFA_CHALLENGED,
        LOGIN_FAILED,
        LOGOUT,
        LOGOUT_ALL,
        SESSION_REVOKED_BY_STAFF,
        PASSWORD_CHANGED,
        PASSWORD_RESET,
        ACCOUNT_LOCKED,
        STAFF_PROVISIONED,
        STAFF_UPDATED,
        STAFF_PERMISSIONS_CHANGED,
        RISK_RULES_RUN,
        FLAG_CREATED,
        FLAG_RESOLVED,
        ACCOUNT_RESTRICTED,
        ACCOUNT_REINSTATED,
    }
)


class UnknownAuditEvent(ValueError):
    pass


def record(
    db: Session,
    *,
    event_type: str,
    subject_type: str,
    subject_id: str,
    actor_id: str | None = None,
    actor_role: str | None = None,
    institution_id: str | None = None,
    detail: dict[str, Any] | None = None,
    source_ip: str | None = None,
    user_agent: str | None = None,
) -> PlatformAuditEvent:
    """Append one event.

    Does not commit. The caller's transaction decides when the event becomes
    durable, so an action that rolls back leaves no audit row claiming it
    happened.
    """
    if event_type not in KNOWN_EVENT_TYPES:
        raise UnknownAuditEvent(f"Unregistered audit event type: {event_type}")

    event = PlatformAuditEvent(
        id=f"pae_{uuid.uuid4().hex[:24]}",
        actor_id=actor_id,
        actor_role=actor_role,
        institution_id=institution_id,
        event_type=event_type,
        subject_type=subject_type,
        subject_id=subject_id or "",
        detail_json=json.dumps(detail or {}, default=str),
        source_ip=source_ip,
        user_agent=user_agent,
        occurred_at=datetime.utcnow(),
    )
    db.add(event)
    return event


def request_context(request: Any) -> dict[str, Any]:
    """Extract IP and user agent from a request, if it has any.

    Kept here so the same pair is recorded everywhere rather than each call site
    inventing its own.
    """
    if request is None:
        return {}

    forwarded = request.headers.get("x-forwarded-for") if request.headers else None
    client = request.client.host if getattr(request, "client", None) else None
    source_ip = None
    if forwarded:
        source_ip = forwarded.split(",")[0].strip()
    elif client:
        source_ip = client

    return {
        "source_ip": source_ip,
        "user_agent": request.headers.get("user-agent") if request.headers else None,
    }