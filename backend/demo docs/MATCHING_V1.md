# Sura Matching v1

## Purpose and boundary

Matching v1 recommends verified vendors to an authenticated individual before
they create a Sura Lock. It is an explainable, deterministic advisory tool.
It does not select a vendor, create a Lock, enrol a member, send an invite, or
move money.

```http
GET /v1/app/recommendations/vendors?category=electronics&target_amount=10000&limit=5
Authorization: Bearer <individual-access-token>
```

`target_amount` is the expected total vendor redemption/payout, not one
member's recurring contribution. All query parameters are optional except that
when present, `target_amount` must be positive and `limit` must be from 1 to
20.

## Ranking rules

Each result has a score from 0 to 100 and reasons that account for every
point.

| Factor | Points | Source |
|---|---:|---|
| Sura verification | 30 | A vendor must be verified to be listed. |
| Category fit | 30 exact, 15 neutral, 0 mismatch | Optional request category and vendor category. |
| Amount fit | 20 close, 14 in range, 10 neutral, 6 outside range | Target payout compared with prior Sura redemption amounts. |
| In-Sura redemption history | 20 completed, 10 no history, 8 mixed | Sura's recorded redemption status only. |

There is no location feature because Sura does not currently store verified
vendor location data. There is no external fulfilment claim: a settled Sura
redemption is not proof that a merchant delivered external goods or services.
Both limits are returned in `unavailable_signals` so the PWA can explain them
honestly.

## Group boundary

Sura Lock is private and pre-invited. There is deliberately no endpoint that
lists or ranks groups a member could join: exposing that would reveal private
group membership and contradict the invite-only Lock contract. The existing
Lock preview endpoint is the only group-planning tool:

```http
POST /v1/app/commitments/lock-preview
```

It validates a selected group and returns its deterministic payout plan. Group
health remains a separate Phase 8 advisory contract; it must not be folded
into vendor matching or used to make an automatic payment/credit decision.
