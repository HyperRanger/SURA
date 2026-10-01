# Rotating Lock Lifecycle v1

This is the durable lifecycle contract for the implemented rotating Sura Lock.
It applies to the MVP only; bank settlement remains simulated and Sura Float is
not part of this flow.

## Cycle policy

- A Lock stores `first_cycle_due_at`, `current_cycle_due_at`, and its agreed
  `grace_period_hours` (default: 72, maximum: 168).
- New clients should supply a future first deadline. Older clients remain
  compatible: the server derives one from the selected weekly or monthly
  frequency.
- `active` means the current cycle is not yet overdue.
- `overdue` means the deadline passed but the grace window is still open.
- `missed` means the grace window ended before the pooled cycle was fully
  funded. No payout or voucher is created.
- Contributions remain permitted in `overdue` and `missed` states. Once the
  pool is complete, the activity log records `cycle_recovered`, then the normal
  paid/voucher flow continues.
- A support case changes the commitment to `under_review`; contributions and
  redemption are paused until an authorised bank staff member resolves it.

## Membership policy

- Only an invited member may decline, and only while the commitment is pending.
- Only the creator may replace an invited or declined member, and only before
  activation. The replacement must be an individual Sura account with granted
  score-processing consent.
- Active contributors cannot leave or be removed. This prevents changes to the
  agreed pool or payout order after the commitment has started.
- Cancellation remains creator-only while membership is pending.

## Support cases

Bank staff with `bank:commitments:write` may use:

```text
POST /v1/bank/commitments/{commitment_id}/cases
POST /v1/bank/commitments/{commitment_id}/cases/{case_id}/resolve
```

Cases are tenant-scoped to the commitment creator's bank. They preserve the
commitment's members, payout order, contribution amount, and voucher identity;
they only pause and later resume the normal lifecycle.
