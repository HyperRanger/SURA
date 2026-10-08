"""Durable abuse protection for authenticated contact resolution."""

from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import case, or_
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models import ContactLookupRateLimit
from core.config import get_settings


def _window_start(now: datetime, window_seconds: int) -> datetime:
    timestamp = int(now.timestamp())
    return datetime.utcfromtimestamp(timestamp - (timestamp % window_seconds))


def _insert_for_database(db: Session):
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        return postgresql_insert(ContactLookupRateLimit)
    if dialect == "sqlite":
        return sqlite_insert(ContactLookupRateLimit)
    raise RuntimeError(f"Contact lookup limiting is not configured for database dialect {dialect!r}.")


def consume_contact_lookup(db: Session, requester_user_id: str) -> None:
    """Atomically consume one lookup allowance or return a retryable 429.

    The conditional upsert prevents two concurrent requests from both seeing
    the same remaining allowance. One row per requester is retained, avoiding
    an unbounded event log or storage of searched contacts.
    """
    settings = get_settings()
    if settings.contact_lookup_max_attempts < 1 or settings.contact_lookup_window_seconds < 1:
        raise RuntimeError("Contact lookup rate-limit settings must be positive.")

    now = datetime.utcnow()
    window_started_at = _window_start(now, settings.contact_lookup_window_seconds)
    window_ends_at = window_started_at + timedelta(seconds=settings.contact_lookup_window_seconds)
    limit = settings.contact_lookup_max_attempts
    same_window = ContactLookupRateLimit.window_started_at == window_started_at

    insert = _insert_for_database(db)
    statement = (
        insert.values(
            requester_user_id=requester_user_id,
            window_started_at=window_started_at,
            attempt_count=1,
        )
        .on_conflict_do_update(
            index_elements=["requester_user_id"],
            set_={
                "window_started_at": case(
                    (same_window, ContactLookupRateLimit.window_started_at),
                    else_=window_started_at,
                ),
                "attempt_count": case(
                    (same_window, ContactLookupRateLimit.attempt_count + 1),
                    else_=1,
                ),
            },
            where=or_(
                ContactLookupRateLimit.window_started_at < window_started_at,
                ContactLookupRateLimit.attempt_count < limit,
            ),
        )
        .returning(ContactLookupRateLimit.attempt_count)
    )

    with db.begin():
        attempt_count = db.execute(statement).scalar_one_or_none()

    if attempt_count is not None:
        return

    retry_after = max(1, int((window_ends_at - now).total_seconds()))
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many contact lookups. Try again shortly.",
        headers={"Retry-After": str(retry_after)},
    )
