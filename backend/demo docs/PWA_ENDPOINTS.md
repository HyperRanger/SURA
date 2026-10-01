# PWA backend endpoint inventory

This is the complete API inventory for the Member/Vendor PWA. It deliberately
excludes Bank Portal and machine-integration routes; use
[BANK_PORTAL_ENDPOINTS.md](BANK_PORTAL_ENDPOINTS.md) for those.

Base URL: the deployed API URL supplied by the backend team. Confirm the exact
release at `GET /openapi.json` before integration. Every protected endpoint
uses `Authorization: Bearer <access_token>`.

## Authentication and profile

| Method | Path | Purpose | Access |
|---|---|---|---|
| POST | `/v1/auth/signup` | Create an individual or vendor account and issue an OTP challenge. | Public |
| POST | `/v1/auth/login` | Start phone-based sign-in and issue an OTP challenge. | Public |
| POST | `/v1/auth/verify-otp` | Consume the OTP and return a session token and assigned role. | Public |
| POST | `/v1/auth/demo-token` | Issue a demo token for a supplied demo user ID. Disabled in production. | Demo only |
| GET | `/v1/me` | Read the current profile and assigned role. Use it to choose member or vendor navigation. | Individual or vendor |
| POST | `/v1/logout` | Revoke the current local session; safe to repeat. | Signed-in user |
| POST | `/v1/logout-all` | Revoke every session for the signed-in user. | Signed-in user |
| POST | `/v1/demo/login-as` | Issue a demo role session. Disabled in production. | Demo only |

Signup accepts `role`, `phone`, `name`, `context`, and `terms_accepted`.
Vendor signup additionally needs `business_name` and `business_category`.
Do not decide the role from client state after signup—use `GET /v1/me`.

## Member home, contacts, and vendor discovery

| Method | Path | Purpose | Access |
|---|---|---|---|
| GET | `/v1/app/home` | Member dashboard: profile, own Score, commitments, and next payout context. | Individual |
| POST | `/v1/app/members/resolve` | Resolve one exact contact before a group invitation. Body: `{ "phone": "..." }`. | Individual |
| GET | `/v1/vendors` | List verified vendors available for Lock creation. | Signed-in user |
| GET | `/v1/app/recommendations/vendors` | Optional explainable vendor ranking. Query: `category`, `target_amount`, `limit`. | Individual |

Contact resolution is rate limited. Respect `429` and the `Retry-After` header.
It returns only the matching member ID and first name; it is not a customer
directory search endpoint.

## Sura Lock: create, join, and manage

| Method | Path | Purpose | Access |
|---|---|---|---|
| POST | `/v1/consent` | Record Score-processing consent. Body: `{ "granted": true }`. | Individual |
| POST | `/v1/app/commitments/lock-preview` | Validate a Lock plan without persisting it. | Individual |
| POST | `/v1/commitments/lock` | Create a rotating Lock. Returns `201`, commitment ID, and invite code. | Individual |
| GET | `/v1/commitments` | List the signed-in member’s Locks. | Individual |
| GET | `/v1/commitments/preview?code={invite_code}` | Preview a pending invitation for the intended invitee. | Individual |
| POST | `/v1/commitments/join` | Join an invitation. Body: `{ "invite_code": "SURA-..." }`. | Invited individual |
| POST | `/v1/commitments/{commitment_id}/decline` | Decline an unresolved invitation before activation. | Invited individual |
| POST | `/v1/commitments/{commitment_id}/members/{invited_user_id}/replace` | Replace an unresolved invitee. Body: `{ "replacement_user_id": "..." }`. | Creator only |
| POST | `/v1/commitments/{commitment_id}/cancel` | Cancel a pending Lock. | Creator only |
| GET | `/v1/commitments/{commitment_id}` | Read the authorised member-safe Lock detail, schedule, and current cycle. | Group member |
| GET | `/v1/commitments/{commitment_id}/activity` | Read Lock activity. | Group member |
| GET | `/v1/app/commitments/{commitment_id}/group-health` | Read aggregate advisory group health. | Group member |
| POST | `/v1/commitments/{commitment_id}/contribute` | Record a contribution. | Eligible group member |
| GET | `/v1/commitments/{commitment_id}/cycles/{cycle_number}/voucher` | Read a voucher code and status. | That cycle’s beneficiary only |

The Lock preview and create requests use the same body:

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

For contributions, create one UUID when the user confirms payment and reuse it
only to retry the same request:

```json
{ "amount": 5000, "event_id": "stable-client-uuid" }
```

The same `event_id` and amount returns `200` with `idempotent_replay: true`.
The same ID with another amount returns `409`. The PWA must never calculate
payout order, Score, voucher validity, due state, or group health itself.

## Sura Score

| Method | Path | Purpose | Access |
|---|---|---|---|
| GET | `/v1/score/{user_id}` | Read the signed-in member’s current explainable 0–1000 Sura Score. | Same individual only |
| GET | `/v1/score/{user_id}/history` | Read that member’s immutable Score history. | Same individual only |
| GET | `/v1/score/{user_id}/history/{entry_id}` | Read one immutable Score evidence entry. | Same individual only |

Render the returned breakdown, weights, signals, and `score_version` as stored.
Sura Score is deterministic and explainable; it is not an ML credit decision.

## Vendor terminal

| Method | Path | Purpose | Access |
|---|---|---|---|
| GET | `/v1/app/vendor/overview` | Vendor dashboard: verification state, totals, and recent redemptions. | Authenticated vendor |
| POST | `/v1/vendors/redeem/validate` | Preview a voucher for the authenticated vendor. Body: `{ "voucher_code": "SURA-..." }`. | Authenticated vendor |
| POST | `/v1/vendors/redeem` | Confirm voucher redemption after handover. Same body as validation. | Authenticated vendor |
| GET | `/v1/vendors/redemptions` | List the authenticated vendor’s redemption history. | Authenticated vendor |
| GET | `/v1/vendors/redemptions/{redemption_id}` | Read one merchant-scoped redemption receipt. | Authenticated vendor |

The vendor ID is derived from the session. Never send `vendor_id` during
validation or redemption. The terminal validates first, asks for confirmation,
then redeems. Validation is not settlement.

## Status behaviour

| Status | PWA behaviour |
|---|---|
| `200` / `201` | Render the returned record or success state. |
| `400` / `422` | Show the policy or field validation message. |
| `401` | Clear the session and start sign-in again. |
| `403` | Show no-access, wrong-vendor, or unavailable state; do not auto-retry. |
| `404` | Show missing/invalid invitation, voucher, or receipt state. |
| `409` | Show duplicate contribution or already-redeemed conflict. |
| `429` | Respect `Retry-After`; especially for contact resolution. |

## Intentionally not in the PWA contract

- Bank Portal operations, bank API keys, webhooks, and staff administration.
- Vendor verification (`POST /v1/vendors/verify`), which is an authorised
  back-office workflow, not a vendor self-verification screen.
- Sura Float, credit applications, real bank-rail settlement, group discovery,
  automated risk decisions, or real outbound webhook delivery.
