# Sura Bank Portal — Screen Specification

## Purpose

The Bank Portal is the secure, web-based operational surface for a partner bank. It lets authorised bank staff review Sura customers, understand explainable score decisions, monitor Sura Lock activity, manage risk flags, inspect simulated settlements, and integrate their systems through API keys and webhooks.

Sura remains non-custodial: the bank owns the customer relationship and moves money on its own rails. The portal exposes Sura's decisioning and audit data; it is not a replacement for the bank's core banking system or KYC/AML controls.

## Audience and access

| Role | Access |
|---|---|
| Bank administrator | All portal areas, team access, API keys and webhook configuration. |
| Risk analyst | Customers, commitments, audit log, flags and settlements. No API-key or team management. |
| Integration engineer | Developer Hub, API keys, webhooks and delivery logs. No customer-risk actions. |
| Demo bank user | Read-only seeded data for the live demo. |

All bank routes require bank authentication and role-based access control. A bank may only view customers and records belonging to its institution. Every customer-profile lookup, key change, webhook change, and flag decision should be recorded in an audit log.

## Security rules

- Use bank SSO/OAuth plus MFA in production. The MVP may use a clearly-labelled demo login only.
- Dashboard sessions are human credentials. API keys are machine credentials and must be separate.
- Show an API-key secret or webhook signing secret exactly once at creation. Store only a hash afterwards.
- Mask account identifiers in tables, exports, and routine views: `••••8241`.
- Never expose a user's score to another member or vendor. Bank roles may see it only where their permissions allow.

## Navigation

```text
/bank/login
/bank
  /commitments
    /:id
  /users
    /:id
      /commitments
      /score
      /activity
      /flags
  /audit-log
  /flags
    /:id
  /settlements
  /developers
    /api-keys
    /api-keys/new
    /webhooks
    /webhooks/:id
    /webhooks/:id/deliveries
    /events
  /team
  /settings
```

## Screens

### B1 — Bank login

**Route:** `/bank/login`

- Bank email or institution SSO button.
- Password/MFA step where appropriate.
- A demo-only bank sign-in option, disabled outside the demo environment.
- Clear error, expired-session, and locked-account states.
- Successful login routes to B2.

### B2 — Portfolio overview

**Route:** `/bank`

- Institution name and current environment: sandbox or live.
- Summary cards: active commitments, total contributed, completion rate, open fraud flags, pending settlements.
- Recent-risk and recent-settlement activity.
- Quick links to commitments, customer search, audit log, flags, and Developer Hub.
- Date range selector.

### B3 — Commitment monitoring

**Route:** `/bank/commitments`

- Search by commitment ID, title, vendor, member, or status.
- Filters: active, pending, missed, completed, redeemed; rotating type; new-group or mixed-group.
- Table columns: ID, title, vendor, members, cycle, status, contributed amount, created date.
- Opens B4.

### B4 — Commitment detail

**Route:** `/bank/commitments/:id`

- Read-only commitment summary and vendor lock.
- Payout schedule and beneficiary status per cycle.
- Contributions and payment status by member; never show one member's score to another member, but authorised bank staff may see score context in this portal.
- Genesis/mixed-group decision, cap decision, and the explainable reason.
- Activity timeline: created, joined, contributed, cycle paid, voucher issued, redeemed.
- Links to associated customer profiles and settlement record.

### B5 — Customer search

**Route:** `/bank/users`

- Search by name, phone number, Sura user ID, bank customer ID/account reference, or commitment ID.
- Filter by score tier, verification status, Float eligibility, open flag, commitment status, and institution.
- Masked identifiers in results.
- Columns: customer, masked bank reference, score/tier, verification, active commitments, on-time rate, flags.
- Opens B6.

### B6 — Customer risk profile

**Route:** `/bank/users/:id`

- Name, masked bank customer reference, Sura user ID, profile context, and verification status.
- Current Sura Score, tier, score date, and five-pillar breakdown.
- Sura Lock summary: completed, active, missed/recovered cycles, on-time contribution rate.
- Float eligibility and reason; this remains locked until the required Lock history exists.
- Open flags and recent events.
- Links to B6a–B6d.

### B6a — Customer commitments

**Route:** `/bank/users/:id/commitments`

- All historical and active Locks for this customer.
- Role, payout slot, contribution completion, missed/recovered state, and voucher/redemption outcome.

### B6b — Customer score detail

**Route:** `/bank/users/:id/score`

- Current score and tier.
- Five pillars: commitment behaviour, repayment behaviour, transaction stability, institutional verification, social reliability.
- Score history with point changes and human-readable reasons.
- Explainability view: event, inputs, score before/after, and policy rule used.

### B6c — Customer activity

**Route:** `/bank/users/:id/activity`

- Chronological activity feed: verification, consent, joining, contribution, missed/recovered event, cycle completion, voucher issuance, redemption, score update, and flag event.

### B6d — Customer flags

**Route:** `/bank/users/:id/flags`

- Current and historical flags, severity, originating rule, evidence, status, and resolution.

### B7 — Audit log

**Route:** `/bank/audit-log`

- Cross-customer log of score changes and material decision events.
- Filter by customer, commitment, pillar, date, event type, and actor.
- Export action with confirmation and audit record.
- Links to the underlying customer, commitment, or flag.

### B8 — Risk flags

**Route:** `/bank/flags`

- List of open, dismissed, confirmed, and escalated flags.
- Filter by severity, rule, date, and status.
- Columns: customer, rule, severity, created time, status, assigned analyst.
- Opens B9.

### B9 — Risk flag review

**Route:** `/bank/flags/:id`

- Rule that fired, affected customer, evidence, and event timeline.
- Actions for authorised risk staff: dismiss, confirm, or escalate with a reason.
- Restricted-account impact and review history.

### B10 — Settlement ledger

**Route:** `/bank/settlements`

- Ledger of simulated bank-to-vendor Lock settlements.
- Search by voucher, vendor, customer, commitment, or settlement ID.
- States: pending, settled, failed, reversed where supported.
- Explicit `simulated settlement` labelling for the MVP.

### B11 — Developer Hub home

**Route:** `/bank/developers`

- Link to live API documentation (`/docs`).
- Integration overview, base URL, authentication method, sample request, and environment status.
- Quick links to API keys, webhooks, event catalogue, and delivery logs.

### B12 — API keys

**Route:** `/bank/developers/api-keys`

- Keys by name, environment, scope, prefix, creation date, last-used time, expiry, and status.
- Create, rotate, revoke, and filter actions.
- Never display an existing secret.

### B13 — Create API key

**Route:** `/bank/developers/api-keys/new`

- Key name, environment, expiry, and least-privilege scopes.
- One-time secret reveal with copy action and acknowledgement.
- Clear warning that the secret cannot be retrieved later.

### B14 — Webhook endpoints

**Route:** `/bank/developers/webhooks`

- Registered endpoint URLs, selected events, status, signing-secret rotation date, and last delivery.
- Add, edit, disable, test, and delete actions.

### B15 — Webhook endpoint detail

**Route:** `/bank/developers/webhooks/:id`

- Endpoint URL, event subscriptions, retry policy, status, and signing-secret rotation action.
- Test delivery action with confirmation.
- Link to delivery logs.

### B16 — Webhook deliveries

**Route:** `/bank/developers/webhooks/:id/deliveries`

- Delivery time, event ID/type, response code, attempts, and final state.
- Redacted payload preview, response summary, and retry action for authorised users.

### B17 — Event catalogue

**Route:** `/bank/developers/events`

- Documented event names, example schemas, ordering guarantees, retry behaviour, and signature-verification example.
- MVP event set: `contribution.recorded`, `cycle.paid`, `voucher.issued`, `voucher.redeemed`, `score.updated`, `flag.created`.

### B18 — Bank team

**Route:** `/bank/team`

- Staff list, role, access state, last login, invite, change-role, and revoke-access actions.

### B19 — Institution settings

**Route:** `/bank/settings`

- Institution profile, supported vendor network, sandbox/live configuration, retention notices, and security settings.

## Backend contract required

The current backend has only the beginnings of B2–B11. These endpoints are required before real portal integration:

```text
GET  /v1/bank/overview
GET  /v1/bank/users?q=&bank_customer_id=&tier=&flag_status=
GET  /v1/bank/users/{user_id}
GET  /v1/bank/users/{user_id}/commitments
GET  /v1/bank/users/{user_id}/score
GET  /v1/bank/users/{user_id}/activity
GET  /v1/bank/users/{user_id}/flags
GET  /v1/bank/commitments
GET  /v1/bank/commitments/{commitment_id}
GET  /v1/bank/audit-log
GET  /v1/flags
GET  /v1/flags/{flag_id}
POST /v1/flags/{flag_id}/resolve
GET  /v1/bank/settlements
GET  /v1/bank/api-keys
POST /v1/bank/api-keys
POST /v1/bank/api-keys/{key_id}/rotate
DELETE /v1/bank/api-keys/{key_id}
GET  /v1/bank/webhooks
POST /v1/bank/webhooks
PATCH /v1/bank/webhooks/{webhook_id}
POST /v1/bank/webhooks/{webhook_id}/test
POST /v1/bank/webhooks/{webhook_id}/rotate-secret
GET  /v1/bank/webhooks/{webhook_id}/deliveries
GET  /v1/bank/events
```

