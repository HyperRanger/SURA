# Sura

**The infrastructure of commitment.**

Sura is a backend-first financial infrastructure product for people whose income does not arrive as a monthly salary. It lets a bank or fintech offer structured, vendor-locked group commitments and an explainable behavioural score through its own customer channels and payment rails.

Sura does not custody customer funds, replace a bank as lender of record, or claim to verify a bank settlement. The bank keeps the customer relationship and executes transactions on its own rails; Sura provides the rules, evidence, APIs, and audit trail around the product.

![Status](https://img.shields.io/badge/status-active%20build-D9A441)
![Python](https://img.shields.io/badge/python-3.11%2B-29235C)
![API](https://img.shields.io/badge/API-FastAPI-29235C)
![Database](https://img.shields.io/badge/database-PostgreSQL-29235C)

## Current scope

The implemented MVP is deliberately narrow and demonstrable:

- **Sura Lock:** rotating commitments, consent, invitations, contributions, deterministic beneficiary order, vendor-locked vouchers, and redemption.
- **Sura Score:** a private, rule-based 0–1000 score with a recorded, explainable history.
- **Member/Vendor API:** role-scoped convenience endpoints for the mobile/PWA experience.
- **Bank Portal and integration API:** customer evidence, Score audit data, flags, staff access, sandbox API keys, and webhook configuration.

**Sura Float is roadmap-only and is not implemented.** No Float request, approval, disbursement, repayment, or fee-calendar endpoint should be presented as live.

Some bank activity is simulated for the MVP. Signed webhook *test* deliveries and delivery logs exist, but real outbound domain-event delivery, retry handling, and a production outbox worker are still to be built.

## What the demo proves

```text
Member creates a rotating Lock
  → invited members consent and join
  → members contribute with replay-safe event IDs
  → a paid cycle creates a beneficiary voucher
  → the locked vendor validates and redeems it
  → the bank views the commitment, settlement evidence, audit trail, and Score movement
```

The same commitment is visible from the member, vendor, and bank perspectives. This is the core product claim: one rules engine and API layer, integrated into different customer experiences.

## Product modules

### Sura Lock

Sura Lock is a rules engine for structured commitments. The current MVP supports **rotating** commitments only. A group agrees the member order, each member contributes, and each paid cycle creates a payout that can be redeemed only with the verified vendor selected at creation.

Key safeguards:

- explicit Score-processing consent before commitment creation or joining;
- verified vendor required at creation;
- deterministic payout order and member eligibility rules;
- positive, bounded contributions with durable `event_id` idempotency;
- voucher access restricted to the actual beneficiary;
- redemption determined from the authenticated vendor account, never a client-supplied vendor ID;
- wrong-vendor and already-redeemed voucher rejection;
- activity and audit evidence for member and bank views.

Collective and individual goal commitments are future product work, not supported commitment types today.

### Sura Score

Sura Score is deliberately deterministic and explainable, not a black-box credit model. It produces a score between 0 and 1000 and persists snapshots so a bank can inspect what changed and why.

| Pillar | Weight | Current source |
|---|---:|---|
| Commitment behaviour | 35% | Lock participation, completion, and contribution behaviour |
| Repayment behaviour | 25% | Float repayment behaviour; currently zero because Float is not built |
| Transaction stability | 20% | Recorded activity regularity |
| Institutional verification | 12% | Verified identity signal |
| Social reliability | 8% | Verified peer co-signers, capped at two |

The entry-tier baseline is **120** for a verified person with no other history. Score rules, weights, version, signals, breakdown, reason, and source event are recorded with each history snapshot. A user can see only their own Score; bank access is tenant- and permission-scoped. New Score processing requires current score-processing consent; historical snapshots remain immutable audit evidence.

### Sura Float

Sura Float remains part of the product vision: a small, predictable-fee institutional advance where another authority enforces repayment. It is intentionally outside this MVP. Any Float eligibility field or Score pillar is informational only until a full Float lifecycle exists.

## Architecture

```text
Member / Vendor PWA       Bank Portal Web App       Bank Core System
         │                        │                        │
         └───────────────┬────────┴────────┬───────────────┘
                         │     Sura API     │
                         │     FastAPI      │
       ┌─────────────────┼─────────┬────────┼─────────────────┐
       │ Auth / sessions │ Lock    │ Score  │ Bank / developer │
       │                 │ engine  │ rules  │ APIs and keys    │
       └─────────────────┴─────────┴────────┴─────────────────┘
                                      │
                                 PostgreSQL
                                      │
                  Vendor redemption and bank/webhook events
                         (partly simulated in this MVP)
```

The code follows the same boundary:

- `backend/app/member_vendor/` contains only PWA-specific composition endpoints and response contracts.
- `backend/app/services/` contains reusable Lock, Score, matching, group-health, vendor, and support rules.
- `backend/app/bank/` contains Bank Portal and machine-integration concerns.
- `backend/app/routers/` contains thin shared HTTP routes.
- `backend/alembic/` owns schema evolution; PostgreSQL is the source of durable state.

No PWA or bank route should duplicate Lock, Score, voucher, or redemption decision logic.

## Frontend applications

The repository contains a Next.js frontend in `frontend/`. It is the public Sura product/marketing site today, including the API-health indicator in its footer. It is not a substitute for the two product applications below.

| Experience | Intended users | Frontend status | Backend it consumes |
|---|---|---|---|
| Public Sura site | Partners, judges, and prospective banks | Present in `frontend/` | `GET /health` today; it can link to the live API documentation |
| Member/Vendor PWA | Individual members and verified vendors | API contract and screen specification are ready; product screens are a separate frontend delivery | `/v1/auth/*`, `/v1/commitments/*`, `/v1/score/*`, `/v1/vendors/*`, and `/v1/app/*` |
| Bank Portal web app | Bank staff and partner operations teams | Backend contract is ready; portal screens are a separate frontend delivery | `/v1/bank/*` and `/v1/integrations/*` |

The Member and Vendor experiences belong in one role-aware PWA. An authenticated vendor is routed to vendor operations; an authenticated individual member is routed to Lock, Score, and profile flows. The Bank Portal is a separate web application because it has a different authentication, permission, audit, and developer-integration model.

Frontend responsibilities are presentation, session storage according to the auth contract, input validation for usability, and calling documented APIs. The backend remains authoritative for roles, consent, money/commitment rules, vendor identity, voucher access, scoring, tenant isolation, and permissions.

### Run the public frontend locally

```bash
cd frontend
npm install
Copy-Item .env.example .env.local  # PowerShell
npm run dev
```

Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` to the local or deployed Sura API URL. The public site's health indicator calls `GET /health`. Never place API secrets, bank API keys, or server-only credentials in a `NEXT_PUBLIC_*` variable.

The complete product-screen inventory is in [SCREENS.md](SCREENS.md), with PWA-specific details in [Member/Vendor app screens](<backend/demo docs/MEMBER_VENDOR_APP_SCREENS.md>) and bank workflows in [Bank Portal screens](<backend/demo docs/BANK_PORTAL_SCREENS.md>).

## API surface

Interactive API documentation is generated from the running application at `/docs`. The route families below are the stable backend handoff categories; refer to the dedicated documents for payloads, response examples, and error behaviour.

| Audience | Route family | Purpose |
|---|---|---|
| All clients | `GET /health` | API and database health |
| Members/vendors | `/v1/auth/*`, `GET /v1/me` | Signup, login, OTP verification, session profile |
| Members | `/v1/consent`, `/v1/commitments/*` | Consent, Lock creation, invitations, join, contribution, voucher, activity, and detail |
| Members | `/v1/score/{user_id}*` | Private Score and Score history |
| Vendors | `/v1/vendors/*` | Catalogue, verification, voucher validation, redemption, and redemption history |
| PWA convenience | `/v1/app/*` | Member home, contact resolution, Lock preview, vendor recommendations, group health, vendor overview |
| Bank staff | `/v1/bank/*` | Overview, customer search, Score/Lock evidence, flags, settlements, audit, staff, settings, keys, and webhooks |
| Bank systems | `/v1/integrations/*` | Scoped API-key access to customer Score and commitment data |

All protected routes use the authenticated principal and role checks. Browser clients must send a bearer token where the contract requires it. A contribution retry must reuse the same `event_id`; the same ID with a different amount is rejected.

## Delivery status

| Capability | Status |
|---|---|
| Rotating Lock lifecycle and contribution idempotency | Implemented and tested |
| Consent, invitation, join, voucher privacy, and vendor-locked redemption | Implemented and tested |
| Explainable Sura Score and Score history | Implemented and tested |
| Member/Vendor PWA API contracts | Implemented and documented |
| Deterministic vendor matching recommendations | Implemented; advisory only |
| Group Health signal | Implemented; advisory only, never a fraud label or automatic action |
| Bank Portal operations and tenant-scoped machine reads | Implemented and tested |
| Sandbox API keys and signed webhook test deliveries | Implemented and tested |
| Real event-driven outbound webhook delivery | Not implemented |
| Real bank-rail settlement and reconciliation | Simulated in MVP |
| Sura Float | Not implemented |

## Local development

Requirements: Python 3.11+, PostgreSQL, and a local environment file. Never commit `.env` files or real credentials.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m alembic upgrade head
uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m alembic upgrade head
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` after startup. Use values from [`backend/.env.example`](backend/.env.example) as placeholders only; create all real secrets in the deployment environment.

## Tests and migrations

Run the full backend suite from `backend`:

```bash
python -m pytest tests -q
```

Before deploying a schema change:

```bash
python -m alembic upgrade head
python -m pytest tests -q
```

GitHub Actions runs the test suite on pushes and pull requests. Deployments should proceed only after CI passes. Alembic migrations are applied during the Render build/deploy process against the configured PostgreSQL database.

## Deployment and demo

The deployed service must provide:

- `DATABASE_URL` for the Render PostgreSQL instance;
- `SECRET_KEY`, JWT configuration, and production environment setting;
- Termii values for real one-time-code delivery in production;
- bank MFA and contact-lookup limits;
- no credentials committed to Git.

Use [`backend/demo docs/DEMO_RUNBOOK.md`](<backend/demo docs/DEMO_RUNBOOK.md>) for the walkthrough and [`backend/demo docs/DEMO_DATA.md`](<backend/demo docs/DEMO_DATA.md>) for reproducible seeded records.

## Documentation

| Document | Use it for |
|---|---|
| [Master Blueprint](SURA_MASTER_BLUEPRINT.md) | Full product vision and longer-term architecture |
| [Build Plan](Sura-Build-Plan.md) | Team sequencing and current MVP boundary |
| [PRD](Sura-PRD.md) | Product requirements |
| [TRD](Sura-TRD.md) | Technical requirements and Score specification |
| [PWA API contract](<backend/demo docs/MEMBER_VENDOR_API.md>) | Member/Vendor frontend integration |
| [PWA frontend handoff](<backend/demo docs/PWA_FRONTEND_HANDOFF.md>) | Tokens, payload expectations, error states, and demo data |
| [Bank Portal screens](<backend/demo docs/BANK_PORTAL_SCREENS.md>) | Bank-facing workflows and backend expectations |
| [Bank Portal safety actions](<backend/demo docs/BANK_PORTAL_SAFETY_ACTIONS.md>) | Human-reviewed rule, restriction, session, and staff recovery controls |
| [Matching v1](<backend/demo docs/MATCHING_V1.md>) | Deterministic advisory vendor ranking |
| [Lock lifecycle v1](<backend/demo docs/LOCK_LIFECYCLE_V1.md>) | Deadlines, recovery, invite replacement, and bank review holds |
| [Group Health v1](<backend/demo docs/GROUP_HEALTH_V1.md>) | Advisory group-health contract and limitations |
| [Release readiness](<backend/demo docs/RELEASE_READINESS.md>) | Release and live-demo checklist |

## Team ownership

| Domain | Owner | Boundary |
|---|---|---|
| Authentication, OTP, sessions, and role claims | @olatunjitobiloba | Other domains consume the established principal; they do not recreate authentication. |
| Lock, vendor flows, PWA contracts, deployment | @HyperRanger | Shared business logic stays outside the PWA folder. |
| Score rule engine and Score evolution | @olatunjitobiloba | Rules remain deterministic, versioned, and auditable. |
| Fraud/risk flags | @olatunjitobiloba & @HyperRanger| Group Health is separate advisory product data, not a competing fraud engine. |
| Bank Portal and integration API | @HyperRanger | Tenant isolation, permissions, audit, keys, and developer tooling. |
| Frontend applications | @fisayo-dev &  | Integrates only against documented endpoints; it does not reproduce backend rules. |

`Backend` is the integration branch. `Master` is the production branch and must remain deployable. Changes should be reviewed, tested, and migrated before merging to `Master`.

## License

Built for submission to InnovateX 2026. A licence for use beyond the competition has not yet been decided; treat this repository as all rights reserved to its authors.
