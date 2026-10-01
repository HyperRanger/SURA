# Sura Technical Requirements Document

Version 1.1
Companion to PRD.md. Read that first for scope and priorities.  
Regional pitch date: October 8, 2026

---

## 1. Architecture Overview

Sura is presented to a bank as infrastructure, not an app. Two internal engines sit behind one external API.

The Commitment Engine owns Sura Lock and Sura Float. It is the state machine that moves a commitment through created, contributed, missed, recovered, completed, redeemed.

The Reputation Engine owns Sura Score. It listens to every event the Commitment Engine emits and recalculates a user's score.

For the regional build, both engines live in one FastAPI service. Splitting them into separate services is not worth the complexity at this scale or on this timeline.

Sura never holds funds. For the regional demo, all settlement is simulated by a mock service that behaves like a real bank rail, and this is stated openly during the pitch.

---

## 2. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend API | Python, FastAPI | Fast to build, generates live interactive docs at /docs for free, good for demoing to judges |
| Database | PostgreSQL (SQLite acceptable for local dev only) | Relational integrity matters for ledger-style data |
| ORM and migrations | SQLAlchemy, Alembic | Reviewable, reversible schema changes under time pressure |
| Score logic | Plain Python, rule-based | Explainable by design, not a trained model |
| Auth | JWT, simulated OTP | Enough to demonstrate verified identity without building a full KYC stack |
| Frontend | React, Tailwind CSS | Fast to build a clean, mobile-first UI |
| Hosting, backend and DB | Railway or Render | Fastest path from a push to a public HTTPS URL |
| Hosting, frontend | Vercel | Zero-config deploys |
| Version control | GitHub, one repo, feature branches | Small team, short timeline |

---

## 3. Data Model

This matches the starter scaffold already in the repo (backend/app/models.py). Field types are illustrative; adjust as needed during implementation, but do not rename tables without updating this document.

### users
- id (string, primary key)
- name
- institution_id (foreign key, nullable)
- phone
- verified_at (nullable datetime)

### institutions
- id (string, primary key)
- name
- fee_calendar_json (nullable, not used in the October 8 scope)

### vendors
- id (string, primary key)
- name
- category
- verified_at

### commitments
- id (string, primary key)
- creator_id (foreign key to users)
- type (enum; only "rotating" is exercised for October 8)
- title
- vendor_id (foreign key)
- contribution_amount
- frequency
- cycles
- status
- created_at

### commitment_members
- commitment_id
- user_id
- role (default "contributor")
- joined_at

### commitment_beneficiaries
- id
- commitment_id
- cycle_number
- user_id
- payout_amount
- status (scheduled or paid)

### contributions
- id
- commitment_id
- user_id
- amount
- paid_at

### score_history
- id
- user_id
- score
- breakdown_json
- computed_at

The floats table exists in the schema for forward compatibility with the full blueprint but is not read from or written to by any October 8 code path.

---

## 4. API Specification

Base path: /v1. All requests and responses are JSON. For the regional demo, the
contribution write uses the durable request-body `event_id` contract: a retry
must reuse the same ID and amount. Other writes do not yet implement a generic
`Idempotency-Key` header; that is a production requirement recorded in
`backend/demo docs/DEMO_TO_PRODUCTION.md`.

### POST /v1/commitments/lock

Creates a new rotating commitment.

Request body:

```json
{
  "type": "rotating",
  "title": "string",
  "vendor_id": "string",
  "contribution_amount": 1000,
  "contribution_frequency": "weekly",
  "cycles": 4,
  "members": ["user_id", "user_id2"],
  "missed_cycle_policy": "carry_forward"
}
```

Response, 201:

```json
{
  "commitment_id": "string",
  "type": "rotating",
  "status": "pending_members",
  "invite_code": "string",
  "payout_schedule": [
    { "cycle": 1, "beneficiary_id": "string", "amount": 1000 }
  ]
}
```

The final group must contain at least two distinct people. The payout schedule
returned here must already reflect the anchor and cap rule in section 5.1, not
a naive order-of-invitation assignment. The demo supports weekly and monthly
frequencies and a fixed 72-hour grace window.

### POST /v1/commitments/{id}/contribute

Records one member's contribution against the current cycle.

Request body:

```json
{
  "amount": 1000,
  "event_id": "stable-client-uuid"
}
```

Response, 200: the updated commitment status, and if this contribution completes the current cycle's total, the beneficiary and redemption details for that cycle.

### GET /v1/commitments/{id}

Returns full commitment status, all cycles, and their beneficiaries and paid states.

### POST /v1/vendors/verify

Marks a vendor as eligible for payout redemption. For October 8, this only needs to work against the 2 to 3 seeded demo vendors; it does not need a real onboarding flow.

### GET /v1/score/{user_id}

Returns the current score and its full pillar breakdown for a user. See section 5.2 for the calculation.

Response, 200:

```json
{
  "user_id": "string",
  "score": 82,
  "breakdown": {
    "commitment_behaviour": 0.35,
    "repayment_behaviour": 0.25,
    "transaction_stability": 0.2,
    "institutional_verification": 0.12,
    "social_reliability": 0.08
  },
  "last_updated": "ISO 8601 timestamp"
}
```

---

## 5. Core Business Logic

### 5.1 The anchor and cap rule for rotating commitments

This is the single most important piece of logic in the whole build, because it is both the fraud prevention mechanism and the reason the live demo is able to show a real payout without contradicting its own rules.

The rule, precisely:

1. When a commitment is created, check whether at least one invited member has a Sura Score above the entry-tier baseline (see 5.2).
2. If yes (a mixed group), that member or members are eligible for early payout cycles, ordered by score, highest first. Brand-new members default to the latest cycles.
3. If no (an all-new group, which includes every demo group by definition), the group is treated as a genesis commitment. The system does not assign an order automatically. Instead, the creator specifies the order at creation time (the group self-selects, exactly like a real ajo circle decides today), and the payout amount for cycle 1 only is capped at a low fixed value regardless of the commitment's normal per cycle amount.
4. Once every member has completed one full rotation, the cap no longer applies to any of them in future commitments.

Implementation note: For October 8, the cap can be a simple constant checked at creation time (for example, cycle 1's amount cannot exceed a fixed ceiling if every member is at the entry tier). Do not over-engineer this before the demo works end to end once with the simple version.

### 5.2 Sura Score calculation

The score is a weighted sum, not a trained model. Weights, from the blueprint:

- Commitment behaviour: 35%
- Repayment behaviour: 25%
- Transaction stability: 20%
- Institutional verification: 12%
- Social reliability: 8%

Entry-tier baseline: A newly verified user with no commitment history starts with a score built only from the institutional verification pillar, everything else at zero. This is what the anchor and cap rule in 5.1 checks against.

Recalculation trigger: Recompute a user's score after every contribution, every completed cycle, and every missed contribution. Do not recompute on every API read; only on the events that change it, and store each recalculation as a new row in score_history rather than overwriting.

### 5.3 Vendor lock and redemption

A commitment's vendor_id is fixed at creation and cannot be changed. A redemption event can only be created for a commitment's already linked vendor. There is no code path that allows a payout to be marked as cash. If this constraint is ever relaxed for testing convenience, it must be reverted before the demo, since it is one of the product's core honesty claims.

For the regional demo, a vendor must be verified before a Lock can be created.
The production onboarding flow will allow a user to express interest in an
unverified vendor while keeping the Lock pending and unreleasable until the
vendor has passed verification.

---

## 6. Authentication and Security

- JWT for session tokens. A shared secret is fine for the regional build, stored in an environment variable, never committed to the repo.
- Simulated OTP for identity verification. A hardcoded code accepted in non-production environments is acceptable for October 8. Label this clearly in the code as a demo shortcut, so it is not mistaken for a real security control later.
- No real personal data of actual people beyond the four team members' own test accounts. Use clearly fictional names and numbers for all other demo data.

---

## 7. Environment Setup

Matches the starter scaffold already handed to the team.

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs to confirm the API is running and to test endpoints directly before the frontend is wired up.

Everyone should be able to complete this setup and confirm /health returns {"status": "ok"} by the end of day September 23. If anyone cannot, that is the team's first blocker to solve, before any feature work starts.

---

## 8. Testing Strategy

Given the timeline, testing effort is concentrated where a failure would be visible on stage, not spread evenly.

### Priority 1: test manually every day
The full Flow A through D from the PRD, run start to finish against the real deployed environment, not just locally.

### Priority 2: automated if time allows
The anchor and cap rule (section 5.1), since it is the piece most likely to have a subtle bug that only shows up with a specific group composition.

### Priority 3: skip for October 8
Full unit test coverage, load testing, and anything related to Sura Float.

---

## 9. Deployment Plan

- Backend and database deploy to Railway or Render from the main branch, on every merge.
- Frontend deploys to Vercel, same trigger.
- Keep a known-good deployed version tagged before the final rehearsal on October 7, so there is a fallback to redeploy from if a last-minute change breaks something on October 8 morning.

---

## 10. Task Breakdown by Role and Day

### September 22 to 23, scope lock and setup
- Backend (core): confirm schema matches section 3, get the starter scaffold running against a real Postgres instance, not just SQLite.
- Backend (AI or ML): write the score calculation from section 5.2 as a standalone function with test cases, before wiring it to the API.
- Frontend: set up the React project and routing, no API calls yet.
- UI and UX: wireframe the four screens named in PRD section 7 (create, contribute, redeem, score).

### September 24 to 28, core build
- Backend (core): implement POST /v1/commitments/lock and POST /v1/commitments/{id}/contribute for real, including the anchor and cap rule.
- Backend (AI or ML): wire the score function to real commitment and contribution events, implement GET /v1/score/{user_id}.
- Frontend: build the create and join commitment screens against the real API, using seed data.
- UI and UX: finalize the visual design system, begin the slide deck in parallel.

### September 29 to October 3, full cycle working
- Backend (core): implement vendor verification and redemption, seed the 2 to 3 demo vendors.
- Backend (AI or ML): confirm the score breakdown updates correctly across a full multi-cycle rotation.
- Frontend: build the redemption and score dashboard screens.
- UI and UX: draft the full demo script against the actual working product, not the plan.

### October 4 to 6, integration and polish
- Whole team: run Flow A through D together, daily, fixing whatever breaks. Seed clean, realistic demo data. Finalize the deck.

### October 7 to 8, rehearsal and pitch
- Whole team: at least two full timed rehearsals on October 7. Keep a screen-recorded backup of a full successful run in case of live network issues on October 8.

---

## 11. Technical Risks

- The anchor and cap rule is new logic with no prior implementation to copy from. Build the simplest version that passes the demo script first; refine only if time remains.
- A four-person team building for 17 days has essentially no slack. If Backend (core) falls behind, everything else stalls, since Frontend and Backend AI or ML both depend on the schema and lock endpoint. Protect that dependency above all else.
- Live demos fail on stage more often from network issues than code bugs. Confirm the venue's wifi situation before October 8 and have the screen-recorded backup ready regardless.
