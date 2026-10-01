# Member P0 Backend Contract Audit

Audit date: 2026-09-30  
Audited baseline: `Backend` commit `1fd6665` (`feat(app): complete member vendor PWA backend contract`)

This is an API audit, not a frontend implementation plan. “Ready” means the
server already enforces the required rule and supplies enough data for the
stated P0 screen. “Needs response adjustment” means the underlying business
rule exists, but the response lacks a privacy-safe presentation field the
screen requires. It does **not** authorise duplicate Lock or Score logic in
the PWA.

## Result

| P0 screen / capability | Existing backend contract | Status | Audit finding / Phase 3 action |
|---|---|---|---|
| P2 signup | `POST /v1/auth/signup` | Ready | Auth-owned OTP challenge flow; individual signup requires terms acceptance. |
| P3 login | `POST /v1/auth/login` | Ready | Same-shaped response for known and unknown contacts prevents account enumeration. |
| P4 OTP verification | `POST /v1/auth/verify-otp` | Ready | Returns bearer token, `user_id`, and server-assigned role. |
| P8 demo switcher | `POST /v1/demo/login-as` | Ready for non-production demo | Correctly returns `404` in production. |
| M1 home | `GET /v1/app/home` | Ready | Own profile, own score, own commitments, active count, and next payout are composed server-side. Account-review banners remain risk/fraud-owner work. |
| M3 my commitments | `GET /v1/commitments` | Ready | Returns only the signed-in member’s commitments and their status. Active/Pending/Completed tabs can filter this own-data list client-side. |
| M4 verified vendor catalogue | `GET /v1/vendors` | Ready | Returns verified vendor ID, name, category, and verification state. |
| M4 member lookup | `POST /v1/app/members/resolve` | Ready for the authenticated MVP | Exact contact lookup returns only user ID and first name, and is rate-limited per caller. The PWA must handle `404` and `429` / `Retry-After`. |
| M4 deterministic plan | `POST /v1/app/commitments/lock-preview` | Ready | Validates vendor, member eligibility, cycle count, payout order, and the Genesis cap without writing. Use `can_create` and `blocking_reason`; do not calculate these in the client. |
| M4 create rotating Lock | `POST /v1/commitments/lock` | Ready | Creates only rotating Locks, requires consent, verified vendor, individual members, a server-derived order, and the first-payout cap. |
| M5 invite-code entry | `GET /v1/commitments/preview?code=` | Needs response adjustment | The current preview requires the caller to have been pre-added to the commitment. This supports phone-resolved invitations, but not a generic share-code recipient who has not yet been enrolled. Decide whether share codes are intentionally limited to pre-invited accounts; otherwise add a non-sensitive public invite preview and a controlled enrolment flow. |
| M6 invite preview | same preview endpoint | Needs response adjustment | Title, amounts, schedule, and slot are present. Vendor and member display names are not; only IDs are returned. Add presentation-safe first names and vendor name if the screen must show them. |
| M7 consent | `POST /v1/consent` | Ready | Persists granted/declined score-processing consent; creation and joining enforce it. Consent copy remains frontend/static content. |
| M8 joined confirmation | `POST /v1/commitments/join` | Needs response adjustment | Join state and commitment data are returned. The “who else joined” UI needs privacy-safe first-name display fields rather than raw IDs. |
| M9 commitment overview | `GET /v1/commitments/{id}` | Ready | Returns status, current-cycle progress, schedules, contributions, deadlines, lifecycle state, and display-safe names. The client does not reimplement Lock calculations. |
| M9 schedule | same detail endpoint | Ready | Returns cycle, beneficiary, payout amount, status, and agreed current-cycle deadline. The server owns schedule advancement. |
| M9 members | same detail endpoint | Ready | Returns first names, role, join time, and server-derived current-cycle payment state. Individual lateness labels remain intentionally unsupported. |
| M9 activity | `GET /v1/commitments/{id}/activity` | Ready | Returns chronological commitment events with cycle and safe event details. |
| M10 contribution | `POST /v1/commitments/{id}/contribute` | Ready | Server validates membership, active state, positive/remaining amount, and cycle transitions. The client must send body field `event_id`; it is **not** an `Idempotency-Key` header in this API. |
| M11 contribution receipt/retry | contribution response | Ready | Returns stable `event_id`, `idempotent_replay`, contribution/cycle status, updated commitment state, and rule trace. |
| M12/M13 beneficiary voucher | `GET /v1/commitments/{id}/cycles/{n}/voucher` | Needs response adjustment | Correctly beneficiary-only and supports locked/ready/redeemed state. The response has vendor ID but not vendor display name; there is no voucher expiry in the model, so the PWA must not invent one. QR rendering is frontend work from `voucher_code`. |
| M14 pending cancellation | `POST /v1/commitments/{id}/cancel` | Ready | Creator-only and pending-only, exactly as required. |
| M16 private score | `GET /v1/score/{user_id}` | Ready | Individual role only; the caller may request only their own score, tier, five-pillar breakdown, weights, and version. |
| M17 private score history | `GET /v1/score/{user_id}/history` | Ready | Individual role only; returns newest-first explainable history with immutable entry IDs, source signals, weights, and score version. |
| M18 score history detail | `GET /v1/score/{user_id}/history/{entry_id}` | Ready | Individual role only; returns one immutable Score snapshot for the explainability screen. |

## Phase 3 resolutions

No endpoint was missing for the basic create → join → contribute → voucher →
redeem → score path. Phase 3 resolved the response-contract gaps as follows:

1. **Invitation boundary:** invite codes are restricted to accounts explicitly
   selected by phone before creation. A generic public join-by-code flow is not
   part of this MVP.
2. **Commitment display fields:** member-authorised commitment responses now
   include vendor information and privacy-safe first names. They never expose
   phone numbers or Scores.
3. **Derived UI state:** commitment responses now contain server-derived
   current-cycle payment state and progress. The PWA does not infer lifecycle
   state from raw contribution rows.
4. **No invented time/miss data:** voucher reads explicitly return
   `expires_at: null`; no endpoint claims due dates, individual missed counts,
   or payment lateness without source events. The PWA must hide those labels.

## Confirmed client rules

- `event_id` is a required JSON body field for contributions. Generate it once
  per confirmation attempt and reuse it on retries.
- The PWA never supplies a `vendor_id` to validate or redeem a voucher; the
  authenticated vendor account resolves the merchant server-side.
- Voucher codes appear only in the beneficiary voucher endpoint and the vendor
  terminal flow, never in general commitment data.
- The PWA renders backend Lock decisions. It does not calculate payout order,
  eligibility, score, voucher validity, contribution completion, or the
  Genesis cap.

## Deliberately outside Member P0

- Float application or disbursement.
- Fraud/account-review decisions and risk flags (separate teammate-owned
  domain).
- Notifications, logout/refresh-token mechanics, profile settings, and score
  history entry detail (P1/P2 or auth-owner work).
- Automatic matching, group-risk enforcement, or machine-learning decisioning.
