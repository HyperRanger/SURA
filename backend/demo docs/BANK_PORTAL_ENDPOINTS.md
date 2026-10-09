# Bank Portal and bank integration endpoint inventory

This is the complete contract for the Bank Portal web application and a bank’s
server-to-server Sura API integration. It deliberately excludes Member/Vendor
PWA routes; use [PWA_ENDPOINTS.md](PWA_ENDPOINTS.md) for those.

## Authentication

Bank Portal calls use `Authorization: Bearer <access_token>` after MFA. Machine
integration calls use `X-Sura-API-Key: <secret>` and never use a portal session.

| Method | Path | Purpose | Access |
|---|---|---|---|
| POST | `/v1/bank/login` | Start staff email/password sign-in. | Public |
| POST | `/v1/bank/login/verify` | Verify MFA code and return the portal session. | Public challenge holder |
| POST | `/v1/bank/logout` | Revoke the current local Bank Portal session. | Bank session |
| POST | `/v1/bank/password` | Change the signed-in staff member’s password. | Local Bank Portal staff |
| POST | `/v1/bank/demo-login` | Issue a demo Bank Portal session. Disabled in production. | Demo only |

## Portfolio overview and customers

All routes in this section are tenant-scoped by the bank identity in the
session. A bank can never read another bank’s customers.

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/v1/bank/overview` | `bank:overview:read` | Portfolio totals, including the simulated bank-owned `portfolio_available_balance_snapshot`, plus recent settlement/audit activity. Query: `date_from`, `date_to`. |
| GET | `/v1/bank/users` | `bank:users:read` | Search/filter customers. Query: `q`, `bank_customer_id`, `score_tier`, `flag_status`, `verified`, `float_eligibility`, `commitment_status`. |
| GET | `/v1/bank/users/{user_id}` | `bank:users:read` | Customer profile, source institution, score summary, consent, and account state. |
| GET | `/v1/bank/users/{user_id}/score` | `bank:users:read` | Current Score plus immutable explainable history. |
| GET | `/v1/bank/users/{user_id}/commitments` | `bank:users:read` | Customer’s Lock evidence and payout status. |
| GET | `/v1/bank/users/{user_id}/activity` | `bank:users:read` | Combined customer activity trail. |
| GET | `/v1/bank/users/{user_id}/flags` | `bank:flags:read` | Review flags for one customer. |

`score_tier` supports `unverified`, `entry`, `building`, and `established`.
`flag_status` supports `open`, `dismissed`, `confirmed`, and `escalated`.
`bank_customer_id` is an exact authorised lookup, not a public account search.

## Lock monitoring and settlement evidence

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/v1/bank/commitments` | `bank:commitments:read` | List Locks. Query: `q`, `status`, `vendor_id`, `member_id`. |
| GET | `/v1/bank/commitments/{commitment_id}` | `bank:commitments:read` | Full tenant-safe Lock evidence, members, contributions, schedule, vouchers, settlement, and cases. |
| GET | `/v1/bank/commitments/{commitment_id}/group-health` | `bank:commitments:read` | Aggregate advisory group health only. |
| POST | `/v1/bank/commitments/{commitment_id}/cases` | `bank:commitments:write` | Open a Lock support case. Body: `{ "reason": "..." }`. |
| POST | `/v1/bank/commitments/{commitment_id}/cases/{case_id}/resolve` | `bank:commitments:write` | Resolve a case. Body: `{ "note": "..." }`. |
| GET | `/v1/bank/settlements` | `bank:settlements:read` | List simulated vendor settlement evidence. Query: `q`, `status`, `vendor_id`, `user_id`, `commitment_id`. |

Group Health is advisory, aggregate, and non-blocking. It does not identify a
member as risky or make a lending decision. Settlement is simulated in this MVP;
the bank’s own rails remain the settlement source of truth.

## Audit, review flags, and account safety actions

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/v1/bank/audit-log` | `bank:audit:read` | Read bank audit entries. Query: `user_id`, `commitment_id`, `event_type`, `actor_id`, `date_from`, `date_to`. |
| POST | `/v1/bank/audit-log/export` | `bank:audit:read` | Export the audit log as CSV. |
| GET | `/v1/bank/flags` | `bank:flags:read` | List review flags. Query: `status`, `severity`, `rule`, `user_id`. |
| GET | `/v1/bank/flags/{flag_id}` | `bank:flags:read` | Read one flag and its review history. |
| POST | `/v1/bank/flags/{flag_id}/resolve` | `bank:flags:write` | Resolve a flag. Body: `{ "action": "dismissed|confirmed|escalated", "note": "..." }`. |
| POST | `/v1/bank/risk-rules/run` | `bank:flags:write` | Evaluate review rules. Body: `{ "user_ids": ["..."] }` or `null` for the tenant book. |
| POST | `/v1/bank/users/{user_id}/restriction` | `bank:flags:write` | Apply `restricted`, `suspended`, or `reinstated` state. Body: `action`, `reason`, optional `flag_id`. |
| GET | `/v1/bank/users/{user_id}/restrictions` | `bank:flags:read` | Read restriction history. |
| POST | `/v1/bank/users/{user_id}/sessions/revoke` | `bank:flags:write` | Revoke every active local session for the customer. |

Rule execution opens review flags; it does not autonomously restrict accounts.
Restrictions are explicit human actions with an audit trail.

## Developer Hub: API keys and webhooks

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/v1/bank/developers` | `bank:developer:write` | Developer Hub overview, API authentication and event catalogue context. |
| GET | `/v1/bank/api-keys` | `bank:developer:write` | List API key metadata; secrets are never returned again. |
| POST | `/v1/bank/api-keys` | `bank:developer:write` | Create a key. Body: `name`, `scopes`, `environment`, optional `expires_at`. Secret is returned once. |
| POST | `/v1/bank/api-keys/{key_id}/rotate` | `bank:developer:write` | Rotate a key; store the newly returned secret immediately. |
| DELETE | `/v1/bank/api-keys/{key_id}` | `bank:developer:write` | Revoke a key. Returns `204`. |
| GET | `/v1/bank/webhooks` | `bank:developer:write` | List webhook subscriptions. |
| POST | `/v1/bank/webhooks` | `bank:developer:write` | Create a webhook. Body: `{ "url": "https://...", "events": ["score.updated"] }`. |
| PATCH | `/v1/bank/webhooks/{webhook_id}` | `bank:developer:write` | Change URL, events, or active/disabled status. |
| DELETE | `/v1/bank/webhooks/{webhook_id}` | `bank:developer:write` | Disable a webhook. Returns `204`. |
| POST | `/v1/bank/webhooks/{webhook_id}/test` | `bank:developer:write` | Send a signed simulated test delivery and record it. |
| POST | `/v1/bank/webhooks/{webhook_id}/rotate-secret` | `bank:developer:write` | Rotate signing secret; store it when returned. |
| GET | `/v1/bank/webhooks/{webhook_id}/deliveries` | `bank:developer:write` | Read delivery log for one webhook. |
| GET | `/v1/bank/events` | `bank:developer:write` | List supported event names. |

Supported event names are `contribution.recorded`, `cycle.paid`,
`voucher.issued`, `voucher.redeemed`, `score.updated`, and `flag.created`.
The MVP supports configuration, signed simulated test delivery, and delivery
logs. It does not yet dispatch real outbound business events with retries.

## Team and tenant settings

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/v1/bank/team` | `bank:team:write` | List bank staff. |
| POST | `/v1/bank/team` | `bank:team:write` | Create staff. Body: `name`, `email`, `role`, `mfa_phone`, `temporary_password`, optional `permissions`. |
| PATCH | `/v1/bank/team/{staff_id}` | `bank:team:write` | Change staff role, permissions, or active/revoked status. |
| POST | `/v1/bank/team/{staff_id}/password-reset` | `bank:team:write` | Reset another staff member’s password. Body: `{ "new_password": "..." }`. |
| PUT | `/v1/bank/team/{staff_id}/permissions` | `bank:team:write` | Replace staff permissions. Body: `{ "permissions": ["..."] }`. |
| GET | `/v1/bank/settings` | `bank:settings:write` | Read bank name, environment, categories, retention, and security settings. |
| PATCH | `/v1/bank/settings` | `bank:settings:write` | Update supported tenant settings. |

Roles are `bank_admin`, `bank_risk_analyst`, and
`bank_integration_engineer`. The backend enforces the permission set; the web
app must not grant capabilities based only on its route or a cached role.

## Bank core system integration

These routes are for a bank backend, not the Bank Portal browser.

| Method | Path | Required API-key scope | Purpose |
|---|---|---|---|
| GET | `/v1/integrations/customers/{user_id}` | `score:read` | Read the tenant-scoped customer profile, including its simulated bank-owned balance snapshot. |
| GET | `/v1/integrations/customers/{user_id}/score` | `score:read` | Read a tenant-scoped customer Score and evidence. |
| GET | `/v1/integrations/customers/{user_id}/commitments` | `commitments:read` | Read a tenant-scoped customer’s Lock evidence. |

## Shared status behaviour

| Status | Portal or integration behaviour |
|---|---|
| `200` / `201` | Render returned data or success state. |
| `204` | Treat the revoke/disable action as complete; there is no response body. |
| `400` / `422` | Show validation or policy detail. |
| `401` | Clear portal session or reject the invalid API key. |
| `403` | Show missing permission or API-key scope; do not retry automatically. |
| `404` | Show no tenant-authorised record exists. |
| `409` | Show current-state conflict and refresh the relevant view. |
