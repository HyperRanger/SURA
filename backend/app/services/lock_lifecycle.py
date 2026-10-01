"""Pure calendar and state rules for the rotating Sura Lock lifecycle."""

from calendar import monthrange
from datetime import datetime, timedelta

SUPPORTED_FREQUENCIES = frozenset({"weekly", "monthly"})


def default_first_due_at(frequency: str, now: datetime) -> datetime:
    if frequency == "weekly":
        return now + timedelta(days=7)
    if frequency == "monthly":
        return advance_due_at(now, frequency)
    raise ValueError("Unsupported contribution frequency.")


def advance_due_at(due_at: datetime, frequency: str) -> datetime:
    if frequency == "weekly":
        return due_at + timedelta(days=7)
    if frequency != "monthly":
        raise ValueError("Unsupported contribution frequency.")
    month = due_at.month + 1
    year = due_at.year
    if month == 13:
        month, year = 1, year + 1
    day = min(due_at.day, monthrange(year, month)[1])
    return due_at.replace(year=year, month=month, day=day)


def deadline_state(*, due_at: datetime | None, grace_period_hours: int, now: datetime) -> str:
    """Return the non-terminal state for an unpaid current cycle."""
    if due_at is None or now <= due_at:
        return "active"
    if now <= due_at + timedelta(hours=grace_period_hours):
        return "overdue"
    return "missed"
