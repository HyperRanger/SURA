"""Rule-based risk flags and account restriction decisions.

The rule engine is deliberately boring. Each rule is a function that reads the
database and returns a finding or ``None``, and every finding names the exact
rows it looked at in ``evidence``. A rule can therefore be argued with, replayed
and audited, which a score or a model output cannot.

Two boundaries keep this honest:

**Rules raise flags. They never move money or change a score.** A finding opens
work for a human at the bank. The only automatic effect in the whole system is
that a *restriction* blocks contributions and redemption, and a restriction is
only ever written by a named staff member through ``apply_restriction``.

**A rule never reads anything outside the bank's own tenant.** Every query filters
on ``bank_id``, so running the engine for one bank cannot surface another bank's
member.
"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.bank.models import AccountRestriction, BankAuditEvent, RiskFlag
from app.models import (
    Commitment,
    CommitmentMember,
    Contribution,
    Redemption,
    ScoreHistory,
    User,
    Voucher,
)
from app.services import audit

# Severity is a closed set. A free-text severity lets a typo silently become an
# unreviewable flag that no dashboard filter matches.
FLAG_SEVERITIES = frozenset({"low", "medium", "high", "critical"})
FLAG_ACTIONS = frozenset({"dismissed", "confirmed", "escalated"})
RESTRICTION_ACTIONS = frozenset({"restricted", "suspended", "reinstated"})

# States in which money may move. Read on every contribution and redemption.
ACCOUNT_STATUSES = frozenset({"active", "restricted", "suspended"})
TRANSACTING_STATUSES = frozenset({"restricted", "suspended"})


@dataclass(frozen=True)
class Finding:
    """One rule's conclusion about one member."""

    rule: str
    severity: str
    summary: str
    evidence: dict


def _window_start(days: int) -> datetime:
    return datetime.utcnow() - timedelta(days=days)


# --- rules -------------------------------------------------------------------
# Each returns zero or more Findings for a single member. A rule must be pure
# with respect to the database: read, decide, return.
#
# `user` has already been resolved through `User.bank_id == bank_id`, and user
# ids are unique across the platform, so scoping by `user.id` is tenant-safe for
# tables that hang off a member. Tables that have their own ``bank_id`` are
# filtered on it anyway: it is the boundary the tables themselves declare, and a
# rule that quietly relies on id uniqueness instead stops being safe the moment
# a member row is ever shared between institutions.
#
# Rules still never restrict. They open a flag for a human.


def _rule_missed_contributions(db: Session, user: User) -> list[Finding]:
    """Two or more shortfall contributions in 90 days.

    A shortfall is a recorded contribution below the commitment's required
    amount. This is observable behaviour, not an accusation about intent.
    """
    rows = (
        db.query(Contribution)
        .join(Commitment, Commitment.id == Contribution.commitment_id)
        .filter(
            Contribution.user_id == user.id,
            Contribution.paid_at >= _window_start(90),
        )
        .all()
    )
    shortfalls = []
    for row in rows:
        commitment = db.get(Commitment, row.commitment_id)
        if commitment is not None and row.amount < commitment.contribution_amount:
            shortfalls.append(
                {
                    "contribution_id": row.id,
                    "commitment_id": row.commitment_id,
                    "amount_paid": row.amount,
                    "amount_required": commitment.contribution_amount,
                    "cycle_number": row.cycle_number,
                    "paid_at": row.paid_at.isoformat() if row.paid_at else None,
                }
            )

    if len(shortfalls) < 2:
        return []

    return [
        Finding(
            rule="missed_contributions",
            severity="high" if len(shortfalls) >= 3 else "medium",
            summary=f"{len(shortfalls)} contributions below the required amount in 90 days.",
            evidence={"shortfalls": shortfalls, "window_days": 90},
        )
    ]


def _rule_repeated_failed_logins(db: Session, user: User) -> list[Finding]:
    """Failed OTP verifications against this account in a short window.

    Counts audit rows rather than attempts, because the challenge row is consumed
    on success and a failed attempt is the only durable trace of a guess.
    """
    rows = (
        db.query(BankAuditEvent)
        .filter(
            BankAuditEvent.bank_id == user.bank_id,
            BankAuditEvent.subject_type == "user",
            BankAuditEvent.subject_id == user.id,
            BankAuditEvent.event_type.in_(["customer_login_failed", "otp_verify_failed"]),
            BankAuditEvent.occurred_at >= _window_start(7),
        )
        .all()
    )
    if len(rows) < 5:
        return []

    return [
        Finding(
            rule="repeated_failed_logins",
            severity="medium",
            summary=f"{len(rows)} failed sign-in attempts against this account in 7 days.",
            evidence={
                "attempt_count": len(rows),
                "window_days": 7,
                "attempt_ids": [row.id for row in rows],
            },
        )
    ]


def _rule_score_decline(db: Session, user: User) -> list[Finding]:
    """A fall of 150 points or more across the last 30 days.

    Reads persisted score history rather than recomputing, so the flag reflects
    what the member's score actually did at the time.
    """
    rows = (
        db.query(ScoreHistory)
        .filter(
            ScoreHistory.bank_id == user.bank_id,
            ScoreHistory.user_id == user.id,
            ScoreHistory.computed_at >= _window_start(30),
        )
        .order_by(ScoreHistory.computed_at.asc())
        .all()
    )
    if len(rows) < 2:
        return []

    earliest, latest = rows[0], rows[-1]
    decline = earliest.score - latest.score
    if decline < 150:
        return []

    return [
        Finding(
            rule="score_decline",
            severity="high" if decline >= 250 else "medium",
            summary=f"Score fell {decline} points in 30 days.",
            evidence={
                "score_before": earliest.score,
                "score_after": latest.score,
                "decline_points": decline,
                "window_days": 30,
                "first_computed_at": earliest.computed_at.isoformat() if earliest.computed_at else None,
                "last_computed_at": latest.computed_at.isoformat() if latest.computed_at else None,
            },
        )
    ]


def _rule_unredeemed_voucher_expiry(db: Session, user: User) -> list[Finding]:
    """A ready voucher sitting unredeemed for more than 30 days.

    Signals a stuck payout rather than member misconduct: the money is owed and
    nobody took it, which is exactly the case a bank wants surfaced.
    """
    rows = (
        db.query(Voucher)
        .filter(
            Voucher.beneficiary_id == user.id,
            Voucher.status == "ready",
            Voucher.issued_at <= _window_start(30),
        )
        .all()
    )
    if not rows:
        return []

    return [
        Finding(
            rule="unredeemed_voucher_expiry",
            severity="low",
            summary=f"{len(rows)} vouchers unredeemed for over 30 days.",
            evidence={
                "voucher_ids": [row.id for row in rows],
                "amounts": [row.amount for row in rows],
                "oldest_issued_at": min(row.issued_at for row in rows).isoformat()
                if min(row.issued_at for row in rows)
                else None,
            },
        )
    ]


def _rule_repeated_commitment_abandonment(db: Session, user: User) -> list[Finding]:
    """Three or more commitments this member joined and never completed."""
    memberships = db.query(CommitmentMember).filter(CommitmentMember.user_id == user.id).all()
    abandoned = []
    for membership in memberships:
        commitment = db.get(Commitment, membership.commitment_id)
        if commitment is None:
            continue
        if commitment.status in {"cancelled", "failed", "expired"} and membership.role != "invited":
            abandoned.append({"commitment_id": commitment.id, "status": commitment.status})

    if len(abandoned) < 3:
        return []

    return [
        Finding(
            rule="commitment_abandonment",
            severity="medium",
            summary=f"{len(abandoned)} commitments ended without completing.",
            evidence={"commitments": abandoned},
        )
    ]


def _rule_redemption_velocity(db: Session, user: User) -> list[Finding]:
    """More settled redemptions in 48 hours than a completed cycle would produce.

    This is the one rule that reads payout behaviour rather than participation.
    It raises a flag for review; it never reverses a redemption.
    """
    rows = (
        db.query(Redemption)
        .filter(
            Redemption.beneficiary_id == user.id,
            Redemption.redeemed_at >= datetime.utcnow() - timedelta(hours=48),
        )
        .all()
    )
    distinct_cycles = {(row.commitment_id, row.cycle_number) for row in rows}
    if len(distinct_cycles) < 3:
        return []

    return [
        Finding(
            rule="redemption_velocity",
            severity="high",
            summary=f"{len(distinct_cycles)} cycles settled within 48 hours.",
            evidence={
                "distinct_cycles": len(distinct_cycles),
                "redemption_ids": [row.id for row in rows],
                "window_hours": 48,
            },
        )
    ]


RULES: tuple[Callable[[Session, User], list[Finding]], ...] = (
    _rule_missed_contributions,
    _rule_repeated_failed_logins,
    _rule_score_decline,
    _rule_unredeemed_voucher_expiry,
    _rule_repeated_commitment_abandonment,
    _rule_redemption_velocity,
)

RULE_SEVERITIES = {rule.__name__.replace("_rule_", ""): "medium" for rule in RULES}


# --- engine ------------------------------------------------------------------


def _open_flag_exists(db: Session, bank_id: str, user_id: str, rule: str) -> bool:
    """True when this bank already has an open flag for the same rule and member.

    This is what makes the engine safe to run repeatedly. Without it, every run
    would open a fresh duplicate flag and the review queue would fill with copies
    of decisions already made.
    """
    return (
        db.query(RiskFlag)
        .filter(
            RiskFlag.bank_id == bank_id,
            RiskFlag.user_id == user_id,
            RiskFlag.rule == rule,
            RiskFlag.status == "open",
        )
        .count()
        > 0
    )


def evaluate_member(db: Session, bank_id: str, user: User) -> list[Finding]:
    """Run every rule for one member and return what fired.

    Pure: no writes. ``run_rules`` decides which findings become flags.
    """
    findings: list[Finding] = []
    for rule in RULES:
        findings.extend(rule(db, user))
    return findings


def run_rules(db: Session, bank_id: str, user_ids: list[str] | None = None) -> dict:
    """Evaluate rules and open a flag for each new finding.

    Returns a summary rather than the rows, so a caller can report what happened
    without being handed a handle on the write path.
    """
    members = (
        db.query(User)
        .filter(User.bank_id == bank_id)
        .filter(User.id.in_(user_ids) if user_ids else True)
        .all()
    )

    created: list[dict] = []
    for member in members:
        for finding in evaluate_member(db, bank_id, member):
            if finding.severity not in FLAG_SEVERITIES:
                # A rule returning an unknown severity is a bug in the rule, and
                # refusing to write it is better than writing a flag no filter
                # will ever match.
                raise HTTPException(
                    status_code=500,
                    detail=f"Rule {finding.rule} returned an invalid severity.",
                )
            if _open_flag_exists(db, bank_id, member.id, finding.rule):
                continue
            flag = RiskFlag(
                id=str(uuid.uuid4()),
                bank_id=bank_id,
                user_id=member.id,
                rule=finding.rule,
                severity=finding.severity,
                status="open",
                evidence_json=json.dumps(
                    {"summary": finding.summary, **finding.evidence}
                ),
            )
            db.add(flag)
            created.append(
                {
                    "flag_id": flag.id,
                    "user_id": member.id,
                    "rule": finding.rule,
                    "severity": finding.severity,
                }
            )

    db.commit()
    return {
        "members_evaluated": len(members),
        "rules_run": [rule.__name__.replace("_rule_", "") for rule in RULES],
        "flags_created": created,
        "flags_created_count": len(created),
    }


# --- restriction decisions ---------------------------------------------------


def _write_audit(db: Session, bank_id: str, actor_id: str, event_type: str, subject_type: str, subject_id: str, details: dict | None = None) -> None:
    db.add(
        BankAuditEvent(
            id=str(uuid.uuid4()),
            bank_id=bank_id,
            actor_id=actor_id,
            event_type=event_type,
            subject_type=subject_type,
            subject_id=subject_id,
            detail_json=json.dumps(details or {}),
            occurred_at=datetime.utcnow(),
        )
    )


def _write_platform_audit(
    db: Session,
    event_type: str,
    subject_type: str,
    subject_id: str,
    *,
    actor_id: str | None = None,
    actor_role: str | None = None,
    bank_id: str | None = None,
    detail: dict | None = None,
) -> None:
    """Mirror an event at platform scope.

    Same event type, same transaction. A risk decision reviewed at platform level
    has to be visible without a cross-tenant read of the bank trail, and the two
    trails roll back together if the decision does.
    """
    audit.record(
        db,
        event_type=event_type,
        subject_type=subject_type,
        subject_id=subject_id,
        actor_id=actor_id,
        actor_role=actor_role,
        institution_id=bank_id,
        detail=detail,
    )


def apply_restriction(
    db: Session,
    bank_id: str,
    actor_id: str,
    user_id: str,
    action: str,
    reason: str,
    *,
    evidence: dict | None = None,
    flag_id: str | None = None,
) -> dict:
    """Restrict, suspend or reinstate one member of this bank.

    A reason is mandatory. The decision is shown to the member and is audited, so
    a restriction nobody can explain is not a usable control.
    """
    if action not in RESTRICTION_ACTIONS:
        raise HTTPException(
            status_code=400,
            detail="Restriction action must be restricted, suspended or reinstated.",
        )

    member = db.query(User).filter(User.id == user_id, User.bank_id == bank_id).one_or_none()
    if member is None:
        raise HTTPException(status_code=404, detail="Customer not found for this bank.")

    if flag_id is not None:
        flag = (
            db.query(RiskFlag)
            .filter(RiskFlag.id == flag_id, RiskFlag.bank_id == bank_id)
            .one_or_none()
        )
        if flag is None:
            raise HTTPException(status_code=404, detail="Risk flag not found.")

    if action == "reinstated":
        if member.account_status == "active":
            raise HTTPException(status_code=409, detail="This account is already active.")
        member.account_status = "active"
        member.restriction_reason = None
        member.restricted_by = None
        member.restricted_at = None
        open_restriction = (
            db.query(AccountRestriction)
            .filter(
                AccountRestriction.bank_id == bank_id,
                AccountRestriction.user_id == user_id,
                AccountRestriction.lifted_at.is_(None),
            )
            .order_by(AccountRestriction.created_at.desc())
            .first()
        )
        if open_restriction is not None:
            open_restriction.lifted_at = datetime.utcnow()
            open_restriction.lifted_by = actor_id
    else:
        if member.account_status == action:
            raise HTTPException(
                status_code=409, detail=f"This account is already {action}."
            )
        member.account_status = action
        member.restriction_reason = reason
        member.restricted_by = actor_id
        member.restricted_at = datetime.utcnow()

    record = AccountRestriction(
        id=str(uuid.uuid4()),
        bank_id=bank_id,
        user_id=user_id,
        action=action,
        reason=reason,
        evidence_json=json.dumps(evidence or {}),
        flag_id=flag_id,
        actor_id=actor_id,
    )
    db.add(record)

    _write_audit(
        db,
        bank_id,
        actor_id,
        f"account_{action}",
        "user",
        user_id,
        {"reason": reason, "flag_id": flag_id, "restriction_id": record.id},
    )
    _write_platform_audit(
        db,
        audit.ACCOUNT_REINSTATED if action == "reinstated" else audit.ACCOUNT_RESTRICTED,
        "user",
        user_id,
        actor_id=actor_id,
        bank_id=bank_id,
        detail={"action": action, "restriction_id": record.id, "flag_id": flag_id},
    )
    db.commit()

    return {
        "user_id": user_id,
        "account_status": member.account_status,
        "action": action,
        "reason": reason,
        "restricted_by": actor_id,
        "restricted_at": (
            member.restricted_at.isoformat() if member.restricted_at else None
        ),
        "restriction_id": record.id,
    }


def list_restrictions(db: Session, bank_id: str, user_id: str | None = None) -> list[dict]:
    rows = db.query(AccountRestriction).filter(AccountRestriction.bank_id == bank_id)
    if user_id:
        rows = rows.filter(AccountRestriction.user_id == user_id)
    return [
        {
            "restriction_id": row.id,
            "user_id": row.user_id,
            "action": row.action,
            "reason": row.reason,
            "evidence": json.loads(row.evidence_json),
            "flag_id": row.flag_id,
            "actor_id": row.actor_id,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "lifted_at": row.lifted_at.isoformat() if row.lifted_at else None,
            "lifted_by": row.lifted_by,
            "active": row.lifted_at is None,
        }
        for row in rows.order_by(AccountRestriction.created_at.desc()).all()
    ]


# --- enforcement -------------------------------------------------------------


def assert_can_transact(db: Session, user_id: str) -> None:
    """Refuse a money-moving action when the bank has restricted the member.

    Called at the point of action rather than at sign-in, so a restriction applied
    mid-session takes effect on the next contribution instead of waiting for the
    member to log out.
    """
    member = db.get(User, user_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Account not found.")
    if member.account_status in TRANSACTING_STATUSES:
        raise HTTPException(
            status_code=403,
            detail=(
                "Your account is under review by your bank and cannot move funds right now."
                if member.account_status == "restricted"
                else "Your account is suspended and cannot move funds."
            ),
        )