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
| M4 member selection | `POST /v1/app/members/resolve` | exact phone lookup; returns only `user_id` and first name |
| M4 payout review | `POST /v1/app/commitments/lock-preview` | validates and returns the deterministic plan without storing anything |
| M4 create Lock | `POST /v1/commitments/lock` | rotating commitments only |
| M6 invite preview | `GET /v1/commitments/preview?code={invite_code}` | intended invitee only |
| M7 consent | `POST /v1/consent` | `{ "granted": true }` required before creating or joining |
| M8 join | `POST /v1/commitments/join` | `{ "invite_code": "SURA-..." }` |
| M9 detail | `GET /v1/commitments/{commitment_id}` | member only; no voucher code exposed |
| M9 activity | `GET /v1/commitments/{commitment_id}/activity` | member only |
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

```json
{
  "type": "rotating",
  "title": "Laptop Fund",
  "vendor_id": "vnd_demo_electronics",
  "contribution_amount": 5000,
  "contribution_frequency": "weekly",
  "cycles": 2,
  "members": ["usr_demo_amara", "usr_demo_tunde"],
  "payout_order": ["usr_demo_amara", "usr_demo_tunde"]
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
| V2 dashboard | `GET /v1/app/vendor/overview` | merchant-scoped today totals and recent redemptions |
| V3/V4 validate | `POST /v1/vendors/redeem/validate` | `{ "voucher_code": "SURA-..." }` |
| V4 confirm | `POST /v1/vendors/redeem` | same request; records simulated settlement |
| V7 history | `GET /v1/vendors/redemptions` | merchant-scoped only |

The backend derives the merchant from the authenticated vendor account. The
PWA must not send or choose a `vendor_id` for redemption. A wrong merchant,
already-used code, unavailable code, or invalid code is rejected by the API.
Validation returns the commitment title, voucher details, and beneficiary first
name only; it does not disclose a phone number, score, or full profile.

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
- Automatic vendor/group selection. Matching will begin as an explainable
  recommendation service after the core Lock journey is complete.
- Cycle-risk automation, fraud decisions, or payment verification. The bank is
  the settlement source of truth; future group-health signals are advisory.
- Real outbound event delivery. Webhook configuration and signed simulated
  test deliveries exist for the bank portal, but there is no production
  webhook worker yet.
