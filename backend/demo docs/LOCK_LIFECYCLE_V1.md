# Rotating Lock Lifecycle v1

This is the durable lifecycle contract for the implemented rotating Sura Lock.
It applies to the MVP only; bank settlement remains simulated and Sura Float is
not part of this flow.

## Cycle policy

- A Lock stores `first_cycle_due_at`, `current_cycle_due_at`, a fixed
  72-hour `grace_period_hours`, and one `missed_cycle_policy` selected at
  creation: `cover_shortfall`, `carry_forward`, or `cancel_and_refund`.
- New clients should supply a future first deadline. Older clients remain
  compatible: the server derives one from the selected weekly or monthly
  frequency.
- `active` means the current cycle is not yet overdue.
- `overdue` means the deadline passed but the grace window is still open.
- `missed` means the grace window ended before the pooled cycle was fully
  funded. No payout or voucher is created.
- `cover_shortfall` lets a member who has already met their own contribution
  cover the remaining pooled shortfall after the cycle is missed. The cover is
  capped at that remaining amount. Once fully funded, the activity log records
  `cycle_recovered`, then the normal paid/voucher flow continues.
- `carry_forward` keeps the unpaid cycle open as a recorded obligation.
  Members may make their normal late contributions; a complete pool records
  `cycle_recovered`. Sura does not issue a partial vendor voucher.
- `cancel_and_refund` cancels the Lock at the missed transition and records an
  auditable `refund_instruction_created` activity. In the regional demo this
  is a simulated bank-rail instruction, not proof that a cash refund moved.
- A support case changes the commitment to `under_review`; contributions and
  redemption are paused until an authorised bank staff member resolves it.

## Membership policy

- Only an invited member may decline, and only while the commitment is pending.
- The unresolved-invite replacement route exists as a back-office/demo helper,
  but is intentionally not part of the PWA product journey. Member
  substitution remains out of scope for the product contract pending a proper
  consent and payout-order redesign.
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
