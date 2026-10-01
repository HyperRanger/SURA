# Bank Portal Safety Actions

These Bank Portal endpoints support a human bank-review workflow. They are not
automatic fraud decisions, payment controls, or a substitute for the bank's
own compliance systems.

All requests require a Bank Portal bearer token. The authenticated
`institution_id` determines the bank tenant; a staff member cannot inspect or
act on another bank's customer.

## Rule evaluation

`POST /v1/bank/risk-rules/run`

Runs the existing deterministic rules for the whole bank tenant or a supplied
list of customer IDs. A finding opens a review flag. It never restricts an
account automatically.

```json
{
  "user_ids": ["usr_123", "usr_456"]
}
```

The caller needs `bank:flags:write`.

## Restriction history and human action

`GET /v1/bank/users/{user_id}/restrictions`

Returns the tenant-scoped restriction history. The caller needs
`bank:flags:read`.

`POST /v1/bank/users/{user_id}/restriction`

Creates a human decision. `action` is one of `restricted`, `suspended`, or
`reinstated`; `reason` is required. `flag_id` is optional when the action is
linked to a reviewed flag.

```json
{
  "action": "restricted",
  "reason": "Analyst review required before further account activity.",
  "flag_id": "flag_123"
}
```

The caller needs `bank:flags:write`. The result is written to the bank audit
trail. It does not alter Lock amounts, payout order, vouchers, or settlements.

## Emergency session revocation

`POST /v1/bank/users/{user_id}/sessions/revoke`

Revokes active sessions for a customer belonging to the caller's bank tenant.
The caller needs `bank:flags:write`. This stops account access; it is not a
Lock cancellation or payment reversal.

## Staff credential recovery

`POST /v1/bank/team/{staff_id}/password-reset`

Sets a new local credential for a Bank Portal staff account. It is available
only to the authorised bank-administration flow. External identity-provider
staff do not have a local credential to reset.

## Scope boundary

Risk rules and restrictions are owned by the risk/fraud domain. Group Health
is separate: it is an explainable advisory signal for a Lock group and never
blocks a member, changes a score, or takes an account action by itself.
