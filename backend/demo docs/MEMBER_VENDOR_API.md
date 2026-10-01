# Member and Vendor PWA API Contract

Base URL: configure this as a frontend environment variable, for example
`SURA_API_BASE_URL`. Verify a release with `{baseUrl}/openapi.json` before
pointing the PWA at it. New endpoints in this document become available online
only after this backend slice is committed, merged, and deployed.

All protected endpoints use:

```http
Authorization: Bearer <access_token>
```

This document is the mobile-client contract. The client displays backend
decisions; it does not calculate scores, payout order, voucher validity, or
permission rules.

## Sessions and roles

| Use | Endpoint | Result |
|---|---|---|
| Create an individual or vendor account | `POST /v1/auth/signup` | OTP challenge; vendor signup needs `business_name` and `business_category` |
| Start login | `POST /v1/auth/login` | OTP challenge |
| Complete login | `POST /v1/auth/verify-otp` | bearer token and assigned role |
| Current account | `GET /v1/me` | profile; vendors also receive their merchant record |
| Demo role switch | `POST /v1/demo/login-as` | non-production only |

The API assigns the role. A frontend route does not grant access. Individual
contexts (`student`, `trader`, `freelancer`, `other`) personalise onboarding
only and never change permissions.

### Authentication boundary

The authentication owner controls token lifetime, refresh, OTP delivery, and
logout. The PWA only depends on this response and the Bearer header:

```json
{
  "access_token": "<bearer-token>",
  "token_type": "bearer",
  "user_id": "...",
  "role": "individual"
}
```

After sign-in, call `GET /v1/me` to choose `/app/*` for `individual` or
`/vendor/*` for `vendor`. Never decide a role from frontend form state.

## Member home and Lock

| Screen | Endpoint | Notes |
|---|---|---|
| M1 home | `GET /v1/app/home` | PWA convenience read: profile, own score, own commitments, next payout |
| M3 commitments | `GET /v1/commitments` | authenticated member only |
| M4 vendor selection | `GET /v1/vendors` | verified vendors only |
| M4 vendor recommendations | `GET /v1/app/recommendations/vendors` | optional advisory ranking; member still selects |
| M4 member selection | `POST /v1/app/members/resolve` | exact phone lookup; returns only `user_id` and first name |
| M4 payout review | `POST /v1/app/commitments/lock-preview` | validates and returns the deterministic plan without storing anything |
| M4 create Lock | `POST /v1/commitments/lock` | rotating commitments only |
| M6 invite preview | `GET /v1/commitments/preview?code={invite_code}` | intended invitee only |
| M7 consent | `POST /v1/consent` | `{ "granted": true }` required before creating or joining |
| M8 join | `POST /v1/commitments/join` | `{ "invite_code": "SURA-..." }` |
| M8 decline | `POST /v1/commitments/{commitment_id}/decline` | invited member, while pending only |
| M8 replace invitee | `POST /v1/commitments/{commitment_id}/members/{invited_user_id}/replace` | creator only; `{ "replacement_user_id": "..." }`, before activation only |
| M9 detail | `GET /v1/commitments/{commitment_id}` | member only; no voucher code exposed |
| M9 activity | `GET /v1/commitments/{commitment_id}/activity` | member only |
| M9 group health | `GET /v1/app/commitments/{commitment_id}/group-health` | member-only, aggregate advisory signal |
| M10 contribute | `POST /v1/commitments/{commitment_id}/contribute` | `{ "amount": 1500, "event_id": "stable-client-uuid" }` |
| M12 voucher | `GET /v1/commitments/{commitment_id}/cycles/{cycle_number}/voucher` | beneficiary only |
| M14 cancel | `POST /v1/commitments/{commitment_id}/cancel` | creator, while pending only |

### Wizard request sequence

1. Call `GET /v1/vendors` and select only a returned vendor.
2. For each known contact, call `POST /v1/app/members/resolve`.
3. Call `POST /v1/app/commitments/lock-preview` whenever members, amount,
   cycles, or payout order changes. Render its schedule directly.
4. Record consent with `POST /v1/consent` if it has not been granted.
5. Submit the same payload to `POST /v1/commitments/lock` only after review.

### Invitation boundary

A Lock invite code is for members selected before creation. The creator resolves
each member’s exact contact, includes the returned `user_id` in `members`, and
the backend records that person as `invited`. Only that invited member can
preview or join the code. Do not build an open public join-by-code flow around
this contract.

```json
{
  "type": "rotating",
  "title": "Laptop Fund",
  "vendor_id": "vnd_demo_electronics",
  "contribution_amount": 5000,
  "contribution_frequency": "weekly",
  "cycles": 2,
  "members": ["usr_demo_amara", "usr_demo_tunde"],
  "payout_order": ["usr_demo_amara", "usr_demo_tunde"],
  "first_cycle_due_at": "2026-10-10T12:00:00Z",
  "grace_period_hours": 72
}
```

The creator must appear in `members`; `cycles` must equal the member count.
The backend is the source of truth for ranking and the first-payout cap. Enable
the final Create action only when preview returns `can_create: true`; otherwise
show its `blocking_reason`.

Contact resolution is authenticated and capped at 10 lookups per member per
15-minute window by default. It returns `429` with `Retry-After` when capped.
The server stores only the caller counter, never searched phone numbers.

Contribution retry rule: generate one stable UUID when the user first taps
Confirm. Reuse that exact `event_id` for retries. A successful replay returns
`200` and `idempotent_replay: true`; reuse with a different amount returns
`409`.

M11 uses the contribution response as its receipt. M13 re-fetches the voucher
endpoint: its state changes from `ready` to `redeemed` after vendor confirmation.

### Commitment display fields

Member-authorised commitment reads include a `vendor` object, privacy-safe
`first_name` fields for members and beneficiaries, and a backend-derived
`current_cycle` summary (`required_total`, `contributed_total`,
`remaining_total`, `paid_member_count`, and `progress_percent`). Render these
values directly. They do not expose phone numbers or Scores.

Voucher reads include `vendor_name`. They also return `expires_at: null` because
the current Lock model has no expiry rule; hide expiry UI rather than inventing
a deadline. Commitment reads expose `current_cycle_due_at`,
`grace_period_hours`, and `missed_cycle_count`; current-cycle member state is
`paid`, `partial`, or `not_paid`.

An unpaid cycle is `active` before its deadline, `overdue` during the grace
period, and `missed` after it. Members may continue contributing after a missed
deadline. Full funding records `cycle_recovered`, pays the beneficiary, and
advances the rotation; no partial payout is ever issued. An invited member may
decline before activation. The creator can replace only an unresolved invitee
before activation, and the replacement must grant score-processing consent and
join normally.

## Vendor matching v1

`GET /v1/app/recommendations/vendors` offers optional, deterministic vendor
recommendations before Lock creation. It accepts optional `category`,
`target_amount` (the total expected redemption/payout), and `limit` query
parameters. Results are advisory and include an explainable score, reasons,
and factor points. The member chooses the vendor and still creates the Lock
through the normal preview/create flow. See [MATCHING_V1.md](MATCHING_V1.md).

There is no group-discovery or group-recommendation endpoint. Lock membership
is private and pre-invited, so exposing other groups would violate that model.

## Group health v1

`GET /v1/app/commitments/{commitment_id}/group-health` returns an explainable
aggregate Lock signal: `low_risk`, `medium_risk`, or `high_risk`, with
confidence, reasons, and counts. It does not identify an individual as risky,
block a contribution, alter a payout, or make a lending decision. See
[GROUP_HEALTH_V1.md](GROUP_HEALTH_V1.md).

## Member Score

| Screen | Endpoint | Notes |
|---|---|---|
| M16 score | `GET /v1/score/{user_id}` | only the authenticated user may request their score |
| M17 history | `GET /v1/score/{user_id}/history` | own explainable score history only |

The current MVP is a deterministic rule engine. The API returns the score,
tier, pillar breakdown, weights, and history evidence. It is not an ML credit
decision and must never be labelled as one in the app.

## Vendor terminal

| Screen | Endpoint | Notes |
|---|---|---|
| V2 dashboard | `GET /v1/app/vendor/overview` | merchant profile/verification state, today totals, and recent redemptions |
| V3/V4 validate | `POST /v1/vendors/redeem/validate` | `{ "voucher_code": "SURA-..." }` |
| V4 confirm | `POST /v1/vendors/redeem` | same request; records simulated settlement |
| V7 history | `GET /v1/vendors/redemptions` | merchant-scoped only |
| V8 receipt detail | `GET /v1/vendors/redemptions/{redemption_id}` | merchant-scoped receipt; returns `404` for another merchant’s record |

The backend derives the merchant from the authenticated vendor account. The
PWA must not send or choose a `vendor_id` for redemption. A wrong merchant,
already-used code, unavailable code, or invalid code is rejected by the API.
Validation returns the commitment title, voucher details, and beneficiary first
name only; it does not disclose a phone number, score, or full profile.

The dashboard `merchant` object is the vendor record assigned to the current
session and includes name, category, and verification state. Redemption history
and receipt details include the commitment title and beneficiary first name,
but never a beneficiary phone number or Score. The redemption response itself
also contains these receipt fields after a successful confirmation.

The terminal always validates first, asks the vendor to confirm handover, then
calls redeem. Validation alone is not settlement.

## Status handling

| Status | Mobile behaviour |
|---|---|
| `200` / `201` | show the returned data or success state |
| `400` | display the returned policy/validation message |
| `401` | clear session and show the session-expired flow |
| `403` | show no-access or voucher-rejected state; do not retry automatically |
| `404` | show missing/invalid invite or voucher state |
| `409` | show already-redeemed or idempotency-conflict state |
| `422` | highlight invalid or missing fields |

## P0 screen map

| Screens | API source |
|---|---|
| P2–P4, V1 | auth endpoints and `GET /v1/me` |
| M1 | `GET /v1/app/home` |
| M3, M9 | commitment list/detail/activity endpoints |
| M4 | vendor list, contact resolution, preview, and Lock creation |
| M5–M8 | invite preview, consent, and join |
| M10–M11 | contribution endpoint and receipt response |
| M12–M13 | beneficiary voucher endpoint; refresh after redemption |
| M16–M17 | own score and score history |
| V2 | vendor overview |
| V3–V6 | vendor validate/redeem endpoints and status responses |

M2 is static education content. QR display/scanning, routing, loading states,
offline behaviour, amount formatting, and visual design are frontend work.

## Seeded demo references

| Item | Value |
|---|---|
| Commitment | `cmt_demo_laptop_rotation` |
| Members | `usr_demo_amara`, `usr_demo_tunde` |
| Vendor | `vnd_demo_electronics` |
| Existing voucher evidence | `SURA-DEMO-LAPTOP-01` |

The seeded voucher is already redeemed. For a live vendor-success or
wrong-vendor recording, create a fresh two-member commitment. See
[DEMO_RUNBOOK.md](DEMO_RUNBOOK.md) for the complete story.

## Deliberately not part of this P0 contract

- Sura Float applications or credit disbursement.
- Automatic vendor/group selection. Matching v1 can recommend vendors only;
  it never selects one or exposes private groups.
- Cycle-risk automation, fraud decisions, or payment verification. The bank is
  settlement source of truth; Group Health v1 is advisory only.
- Real outbound event delivery. Webhook configuration and signed simulated
  test deliveries exist for the bank portal, but there is no production
  webhook worker yet.
