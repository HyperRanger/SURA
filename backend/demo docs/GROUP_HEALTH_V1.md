# Sura Lock Group Health v1

## Purpose

Group Health v1 is a deterministic, explainable view of a rotating Lock's
observed group behaviour. It helps a member understand the group state and
helps a bank analyst decide whether a group deserves manual attention.

It is not fraud detection, a credit decision, payment verification, or an
automatic intervention. It never blocks a contribution, changes payout order,
or moves money.

## PWA endpoint

Only an authenticated individual who belongs to the Lock may read this route:

```http
GET /v1/app/commitments/{commitment_id}/group-health
Authorization: Bearer <member-access-token>
```

## Response contract

```json
{
  "commitment_id": "cmt_demo_laptop_rotation",
  "advisory": true,
  "group_health": "low_risk",
  "confidence": "moderate",
  "reasons": [
    "1 joined member(s) have not recorded a current-cycle contribution. No due-date data exists, so this is not labelled late.",
    "1 cycle(s) have reached a paid or redeemed outcome."
  ],
  "metrics": {
    "commitment_status": "active",
    "member_count": 2,
    "joined_member_count": 2,
    "pending_invitation_count": 0,
    "completed_cycles": 1,
    "missed_cycles": 0,
    "historical_cycle_completion_rate": 1.0,
    "current_cycle_number": 2,
    "current_cycle_due_at": "2026-10-08T12:00:00",
    "current_cycle_grace_period_hours": 72,
    "current_cycle_deadline_state": "active",
    "current_cycle_required_total": 10000,
    "current_cycle_contributed_total": 5000,
    "current_cycle_paid_member_count": 1,
    "current_cycle_partial_member_count": 0,
    "current_cycle_unpaid_member_count": 1
  },
  "unavailable_signals": [
    "external payment-rail settlement",
    "member exit reason"
  ],
  "policy_note": "Advisory only. This result does not approve credit, block a contribution, or change payout order."
}
```

## Classification rules

| Group health | Rule |
|---|---|
| `high_risk` | At least one cycle is recorded as missed, or the current cycle is past its due date and grace period. |
| `medium_risk` | No missed-cycle signal, but the current cycle is overdue, an invitation remains unjoined, or a joined member has made a partial current-cycle contribution. |
| `low_risk` | No missed/overdue deadline signal, incomplete formation, or partial current-cycle contribution. |

Confidence is `limited` with no closed cycles, `moderate` with one or two, and
`strong` with three or more. A low-risk result with limited confidence means
there is not enough history to make a stronger statement.

The API reads the Lock's persisted current-cycle due date and agreed grace
period. It reports deadline state at the group level only; it does not name or
rank an individual member as late. A deadline that has passed grace is an
advisory signal until normal Lock lifecycle processing persists its outcome.

## Bank Portal counterpart

Bank staff with `bank:commitments:read` can view the same aggregate report for
a commitment scoped to their bank:

```http
GET /v1/bank/commitments/{commitment_id}/group-health
Authorization: Bearer <bank-access-token>
```

The report contains counts only. It does not label, rank, or expose a named
individual as risky.
