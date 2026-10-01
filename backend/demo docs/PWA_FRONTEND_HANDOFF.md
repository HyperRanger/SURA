# Member and Vendor PWA Handoff

## Release status

This package describes the completed Member/Vendor P0 backend contract in the
local `Backend` worktree. It is ready for frontend integration, but it is not
yet a production release. Do not point a production PWA build at a route in
this package until the backend change is committed, merged into production,
deployed, and verified through `/openapi.json`.

Set the frontend base URL through an environment variable:

```text
SURA_API_BASE_URL=https://<deployed-sura-api>
```

The canonical detailed contract is [MEMBER_VENDOR_API.md](MEMBER_VENDOR_API.md).
This document is the practical handoff checklist.

## Routing and sessions

All protected calls use:

```http
Authorization: Bearer <access_token>
```

1. Complete the normal auth flow.
2. Call `GET /v1/me`.
3. Route `role: individual` to the member experience and `role: vendor` to
   the vendor terminal.

The client must never grant a role from a signup form or local state. Token
refresh, OTP delivery, and logout are owned by the authentication backend
workstream.

## Screen-to-API summary

| User area | Calls |
|---|---|
| Member home | `GET /v1/app/home` |
| My Locks | `GET /v1/commitments`, `GET /v1/commitments/{commitment_id}`, `GET /v1/commitments/{commitment_id}/activity` |
| Group health | `GET /v1/app/commitments/{commitment_id}/group-health` |
| Create Lock | `GET /v1/vendors`, `POST /v1/app/members/resolve`, `POST /v1/app/commitments/lock-preview`, `POST /v1/consent`, `POST /v1/commitments/lock` |
| Optional vendor recommendations | `GET /v1/app/recommendations/vendors?category=&target_amount=&limit=` |
| Invitations | `GET /v1/commitments/preview?code={invite_code}`, `POST /v1/commitments/join` |
| Contribution receipt | `POST /v1/commitments/{commitment_id}/contribute` |
| Beneficiary voucher | `GET /v1/commitments/{commitment_id}/cycles/{cycle_number}/voucher` |
| Cancel pending Lock | `POST /v1/commitments/{commitment_id}/cancel` |
| Private Score | `GET /v1/score/{user_id}`, `GET /v1/score/{user_id}/history`, `GET /v1/score/{user_id}/history/{entry_id}` |
| Vendor dashboard | `GET /v1/app/vendor/overview` |
| Vendor redemption | `POST /v1/vendors/redeem/validate`, `POST /v1/vendors/redeem` |
| Vendor receipts | `GET /v1/vendors/redemptions`, `GET /v1/vendors/redemptions/{redemption_id}` |

## Non-negotiable client rules

- Generate a UUID once when a member confirms a contribution. Send it as
  `event_id` in the JSON body and reuse it only if that exact payment is
  retried.
- A repeat contribution with the same amount returns `200` with
  `idempotent_replay: true`. The same `event_id` with another amount returns
  `409`; ask the member to contact support or start a new payment attempt.
- Build Lock invitations from contacts resolved before creation. An invite
  code is not a public group-discovery code; only an invited member can view
  or join it.
- Render Lock schedule, cycle progress, payment state, payout order, and
  vendor verification from API responses. Do not calculate them in the PWA.
- A voucher code belongs only in the beneficiary voucher view and the
  authenticated vendor terminal. Never display it in a general commitment
  screen.
- Treat a Score history entry as immutable evidence. Render its stored
  `signals`, `weights`, and `score_version`; do not recalculate or relabel a
  historical score using a newer client rule.
- The vendor terminal never sends a `vendor_id` during validation or
  redemption. The API derives the merchant from the vendor session.
- Validate a voucher, show the handover confirmation, then redeem it.
  Validation alone is not settlement.
- `expires_at: null` means there is no expiry rule in the MVP. Hide expiry UI.

## Expected status behaviour

| Status | Client action |
|---|---|
| `200` / `201` | Render the returned record or success state. |
| `400` | Display the API policy or validation message. |
| `401` | Clear the local session and start sign-in again. |
| `403` | Show an access-denied or wrong-vendor result; do not auto-retry. |
| `404` | Show an invalid/missing invitation, voucher, or receipt state. |
| `409` | Show replay, already-redeemed, or conflicting-state feedback. |
| `422` | Mark request fields using the validation error details. |
| `429` | Respect `Retry-After`, especially for contact resolution. |

## Demo data and recording story

Seed only after migrations are at the latest head:

```powershell
cd backend
python scripts/seed_demo_data.py --reset
```

Use Amara Okafor and Tunde Adeyemi, vendor `vnd_demo_electronics`, and
commitment `cmt_demo_laptop_rotation` for read-only screens. The seeded voucher
has already been redeemed. Create a fresh two-member Lock to record the live
member -> vendor -> bank story. Details are in [DEMO_DATA.md](DEMO_DATA.md) and
[LOCK_P0_ACCEPTANCE.md](LOCK_P0_ACCEPTANCE.md).

## Do not build in this P0 client

- A public join-any-code flow.
- Client-side payout, voucher, score, or permission calculations.
- Per-member due dates, missed-payment counts, or voucher expiry displays;
  those rules are not modelled yet.
- A vendor picker in the redemption request.
- Sura Float, credit applications, group discovery, or automated group-risk
  decisions. Group Health v1 and vendor matching v1 are advisory only; see
  [GROUP_HEALTH_V1.md](GROUP_HEALTH_V1.md) and [MATCHING_V1.md](MATCHING_V1.md).
- A claim that redemption verifies an external payment rail. Settlement is
  simulated in this MVP.

## Release gate before frontend uses the deployed API

1. Run `python -m pytest backend/tests -q` successfully.
2. Confirm one Alembic head and run migrations in the deployment.
3. Deploy the approved backend revision.
4. Check `GET /health`, `GET /docs`, and `GET /openapi.json` on that exact
   deployed base URL.
5. Seed the deployed demo database if the recording needs demo data.
6. Run the full member -> vendor -> bank acceptance journey in
   [LOCK_P0_ACCEPTANCE.md](LOCK_P0_ACCEPTANCE.md).
7. Give the PWA team the verified base URL and this exact commit/release ID.

Only then is the handoff a live integration handoff rather than a local API
contract.
