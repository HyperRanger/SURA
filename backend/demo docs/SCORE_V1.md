# Sura Score v1

Sura Score v1 is a deterministic, rule-based behavioural score from 0 to 1000.
It is not a credit-bureau score, an ML prediction, a fraud decision, or an
automatic lending approval.

## What a snapshot proves

Each persisted score change records the score before and after, the triggering
event and source ID, the five pillar point values, their weights, the raw
persisted input signals, and the version of the rules. A historical snapshot
is immutable: a client must display its stored inputs and version, rather than
recalculate it with a newer rule set.

## Access and consent

- Members can read only their own current score and history.
- Bank staff and machine API clients are tenant-scoped before a customer score
  can be returned.
- A granted `score_processing` consent is required to create new snapshots.
- Withdrawing consent stops future score processing. It does not silently
  rewrite previously recorded audit evidence.

## API contract

```text
GET /v1/score/{user_id}
GET /v1/score/{user_id}/history
GET /v1/score/{user_id}/history/{entry_id}
GET /v1/bank/users/{user_id}/score
GET /v1/integrations/customers/{user_id}/score
```

The member endpoints require an individual session for that same `user_id`.
The last two endpoints require the Bank Portal permission or an appropriately
scoped bank API key.

## Scope boundary

The repayment pillar is present in the stable model but is zero until Sura
Float has a real lifecycle. Float is not part of this MVP and this score must
not be presented as an eligibility or lending decision.
