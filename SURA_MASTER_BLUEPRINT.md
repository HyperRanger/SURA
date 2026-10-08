# SURA

## THE INFRASTRUCTURE OF COMMITMENT.

### AN API FOR BANKS, FINTECHS & FINANCIAL INSTITUTIONS

Product & Build Blueprint

Prepared for InnovateX 2026  ·  Inclusive Finance Track  ·  Ecobank

TEAM
- Backend Engineering
- AI / ML Engineering
- Frontend Engineering
- UI/UX Design & Pitch

September 2026

---

## Contents

1. Executive Summary
2. The Problem
3. The Solution — Sura in Plain English
4. Product Modules
5. The Reputation Engine — Sura Score
6. System Architecture
7. API Reference
8. Recommended Technology Stack
9. Regulatory & Compliance Positioning
10. Revenue Model
11. Stress-Testing Sura
12. Team & Roles
13. Build Plan — Phases & Milestones
14. Demo & Pitch Script
15. Risks & Mitigations

Appendices:
- A. Glossary
- B. Core Data Schema (Sketch)

---

## 01. Executive Summary

Irregular income doesn't mean unreliable character. It just means invisible to a system built around salaries.

A trader who turns over cash daily. A student whose money arrives in one lump sum a term. A freelance musician or developer paid in uneven bursts between gigs. Three completely different lives, all locked out of formal credit for the same reason: none of them has a payslip a bank's underwriting model recognises. Sura turns their actual behaviour — showing up, contributing, finishing what they start — into the data a bank can act on instead.

Sura is not a savings app and not a loan app. It is an API layer that any bank or fintech can plug into their existing systems to offer structured group savings, small predictable-fee advances, and a transparent reputation score — built for anyone whose income doesn't arrive as a monthly salary, whoever they are.

What this document covers:
- the problem Sura solves, and why existing products don't solve it
- the product — Sura Lock, Sura Float, and the shared Sura Score reputation engine
- the technical architecture and full API reference a bank engineer would actually integrate against
- the recommended technology stack for building the MVP inside the hackathon window
- the team structure, task split, build phases, and week-by-week milestones for a team of four
- the pitch, revenue model, and regulatory positioning for the judging panel

At a glance:
- Core modules — Lock + Float
- Shared reputation engine
- Core API endpoints
- Projected default rate on Float

---

## 02. The Problem

### Three lives, one root cause

A trader closes her stall every evening and sets aside what she can. A student's allowance lands once a term and has to stretch across fees that don't wait. A freelance musician or developer gets paid in bursts — a gig here, a project there — with nothing predictable about when the next one lands. None of them has a monthly payslip. That single fact is enough for the formal banking system to treat all three as invisible.

This isn't a hypothetical for our team. One of us plays guitar and takes paid session and cover work; another is a self-taught developer living on project-based income. The gap between “money is coming” and “money is here right now” is something we've felt directly, not just researched.

### Why the obvious fixes don't work

| Common approach | Why it falls short |
|---|---|
| Traditional salary-based lending | Priced for a system with no default protection against irregular income — institutions either avoid informal earners entirely or price credit out of their reach. |
| “AI credit scoring” | A black-box model trained on thin, informal-economy data is hard for a bank's risk team to explain, audit, or defend to a regulator. |
| Generic savings apps | They hold money, but nothing stops a user from withdrawing and spending it — the discipline problem is never actually solved. |
| Ignoring informal earners | The current default. Financial inclusion stays a marketing slogan instead of a working product for the 9 in 10 Nigerians it would actually reach. |

### The opportunity

93% of employed Nigerians work in the informal economy (NESG, 2025), and 58% of that informal workforce is under 34 (Moniepoint, 2025). This isn't a niche gap — irregular income is the default financial life for most young Nigerians, whether they trade, study, or freelance.

The institution that can safely and transparently extend structured financial products to this majority doesn't just do good — it acquires the customer every other bank still treats as unbankable.

---

## 03. The Solution — Sura in Plain English

“Sura turns commitment into financial data.”

Sura takes something that already happens in one form or another — pooling money toward a goal, or covering a small recurring cost — and gives it structure, so that good behaviour becomes something a bank can actually see and reward, no matter what the person's income looks like.

### The commitment journey

- A goal, not a wallet. Someone names a specific target — a sewing machine, a laptop, an audio interface, a deposit — and money can only ever leave the commitment toward that stated purpose.
- Peers, not paperwork. Instead of a credit check, a small group of verified peers joins the commitment and contributes alongside them — the same discipline behind an ajo circle, just with structure underneath it.
- Locked, not liquid. The funds are never available as cash. The system, not willpower, is what prevents misuse.
- Paid to the shop, not the person. When the goal is hit, the money moves straight from the bank to the verified vendor. They walk in, scan a code, and walk out with the goal met — never having touched the cash.

### Who benefits, and how

| For… | Sura means… |
|---|---|
| A trader | A safer, bank-backed alternative to a cash ajo pool that can disappear overnight — same discipline, no risk of a collector running off with the contributions. |
| A student | A structured way to save toward something specific with peers, and a way to cover small mandatory fees without missing a registration deadline. |
| A freelancer | A way to turn irregular gig income into steady progress toward equipment or a goal, and a repayment structure that fits self-enforcing obligations like a subscription or hosting renewal. |
| A vendor | Guaranteed, pre-committed sales — the money is already locked to them before the customer even walks in. |
| A bank | A new, high-engagement product it can launch in weeks by plugging into one API — plus a completely new dataset for underwriting the majority of Nigerians formal credit currently ignores. |

---

## 04. Product Modules

Sura ships as two modules that sit on top of one shared engine. They are built and demoed as one product with two proofs, not three unrelated features bundled together.

### Module 1 — Sura Lock

Programmable financial commitments — not just “everyone saves for one person”.

An early version of this design had a real flaw: if a group contributes and only one member ever receives the payout, that isn't a savings product — it's crowdfunding, and the other members never get their money back. The fix is to make the commitment type explicit and configurable, so Sura never quietly decides who gets free money — it just enforces whatever terms the group agreed to.

| Commitment type | How it works | Example |
|---|---|---|
| Rotating | Members contribute on a fixed schedule; the pooled amount rotates to a different member at each cycle until everyone has received a payout. | A digitised ajo — 5 traders each contribute weekly; each takes a turn receiving the pool. |
| Collective goal | Everyone contributes toward one shared objective that benefits every contributor equally. | 5 roommates pool ₦500,000 toward shared apartment furniture. |
| Individual goal | One member is the named beneficiary; everyone else is explicitly marked as a sponsor, not a saver — Sura never disguises a gift as savings. | Friends pool money as a gift toward one member's audio interface. |

Whatever the type, the underlying mechanics are identical:
- The funds are locked to a vendor, not to a person. No one can withdraw cash at any point, regardless of commitment type.
- Vendors aren't onboarded — they're inherited. A payout can only settle to a merchant already verified on the partner bank's existing acquiring network. Sura doesn't recruit vendors; it restricts payouts to a network the bank already built.
- When a payout point is reached — the goal is hit, or a rotation cycle comes due — a vendor-locked voucher is generated for whoever is entitled to it that cycle.
- Missed contributions are handled without inventing an insurance product. Sura flags the miss, applies whatever rule the group agreed to up front, updates that member's commitment history, and can restrict their eligibility for future commitments. No separate stake pool to manage.

Sura's job isn't deciding who gets free money. Its job is enforcing the commitment: who owes, who contributes, who receives, when they receive it, and what they can spend it on.

### Solving the genesis problem: what if a whole group is new?

A last-slot rule only prevents fraud if the group has at least one member with history to anchor the order. A group where every member is brand new — unavoidable for the platform's very first cohorts, and possible any time a new friend group joins together — needs its own rule, or a rotation can never start at all:

- Mixed group: if a commitment includes at least one member above the entry tier, that member is eligible for an early slot under the normal score-based order. Brand-new members in the same group still default to later slots.
- All-new group: the group self-selects who goes first, exactly like a traditional ajo circle decides today. Sura bounds the platform's exposure instead of removing peer trust from the decision — the first payout in an all-new group is capped at a low fixed amount, regardless of the commitment's actual target.
- Graduation: once a group completes one full rotation together, every member now has commitment history, and the cap lifts for their future commitments.

This is also exactly how the live demo is able to show a real first-cycle payout on stage: a fresh demo group is a textbook all-new group — capped and self-selected by design, not an exception quietly made for the pitch.

### Module 2 — Sura Float

Micro-advances — but only where a real authority enforces repayment.

Float only works where its low-default trick works: something else already enforces the deadline, so Sura doesn't have to.

- For students: small recurring institutional fees — departmental dues, lab fees, exam cards, project supervision levies. A student selects their department and level; Sura has a pre-mapped fee calendar. Unpaid fees block registration, so the university itself becomes the collections mechanism.
- For a freelance developer: a self-enforcing recurring cost like a domain or hosting renewal — miss the payment and the site or service goes down automatically.
- Deliberately excluded from the MVP: tuition, and open-ended personal spending.
- The money never touches the borrower. It transfers directly from the bank to the institution or service being paid.
- The cost of credit is disclosed, not hidden in the framing. Float charges a flat, non-compounding origination fee rather than a rate that scales with delay.

That is disclosed on purpose, not buried — and it sits at roughly a fifth of the 240–336% APR regulators have penalised Nigerian loan apps for charging.

### Why banks want this as an API, not an app

Every Sura Lock contribution and every Sura Float disbursement is a transaction on the bank's own rails. Sura doesn't compete with the bank for the customer relationship — it generates transaction volume and owns none of it.

---

## 05. The Reputation Engine — Sura Score

Traditional credit bureaus say “we don't know you.” Sura Score says “we know you through your consistency and your community.”

It is deliberately not a black-box machine-learning credit model. It is a transparent, rule-based, explainable score — every point on it can be traced back to a specific behaviour.

### What it's built from

| Pillar | Data source | What it proves |
|---|---|---|
| Commitment behaviour (35%) | History of completed Sura Locks | The single strongest predictor: has this person actually finished what they started? |
| Repayment behaviour (25%) | On-time Sura Float repayments | Direct evidence of how they handle a live, real-money obligation. |
| Transaction stability (20%) | 3–6 months of account history | Regular, non-erratic account activity signals a stable financial life. |
| Institutional verification (12%) | Verified identity via student portal, trade association, or gig platform history | Context and identity confirmation. |
| Social reliability (8%) | Peer co-signers from the same verified circle | A light-touch signal, not a punitive one. |

### Cold start: what a brand-new user gets

A score model is only credible if it has an honest answer for someone with zero history — otherwise it's just re-inventing the exclusion it claims to fix. Sura defines an explicit starting tier instead of leaving this undefined:

- Unverified (entry tier): built purely from institutional verification — proof the person is real, nothing more. This is enough to join a Lock commitment.
- Float stays locked at this tier. A new user cannot access Sura Float until they've completed at least one full Lock cycle.
- Rotating commitments default new members to the last payout slot — so a user's first commitment is the one that builds their history, not one that puts the bank's money at risk on a stranger.

### What the score is not

- Not a public score.
- Not an academic or professional judgement.
- Not a replacement for KYC/AML.

---

## 06. System Architecture

Sura is presented to a financial institution as infrastructure, not an app. The bank keeps the customer relationship and the money; Sura provides the decisioning layer that sits between the two engines and the bank's own rails.

### Layer by layer

- Commitment Engine — owns Sura Lock and Sura Float. It is the state machine that moves a commitment through created → contributed → missed → recovered → completed → redeemed.
- Reputation Engine — owns Sura Score. It listens to every event the Commitment Engine emits and recalculates a user's score.
- One API — a single versioned contract the bank touches.
- Custodial position — Sura never holds or custodies funds. It instructs the bank's rails to move money.

### Trust boundaries

For the hackathon build, the “bank rail” and the institution/vendor payout endpoints are simulated — a mock service that behaves like a real settlement rail. This is stated openly in the demo rather than implied.

---

## 07. API Reference

This is the actual contract a bank's engineering team would integrate against. In the MVP, FastAPI generates interactive documentation automatically at /docs.

### Endpoint summary

| Method & path | Purpose | Auth |
|---|---|---|
| POST /v1/commitments/lock | Create a commitment | Bank-signed |
| POST /v1/commitments/{id}/contribute | Record a member's micro-contribution | Bank-signed |
| GET /v1/commitments/{id} | Retrieve commitment status | Bank-signed |
| POST /v1/commitments/float | Request a fee micro-advance | Bank-signed |
| GET /v1/score/{user_id} | Retrieve a user's Sura Score and breakdown | Bank-signed |
| POST /v1/vendors/verify | Verify and lock a vendor for disbursement | Bank-signed |
| GET /v1/institutions/{id}/fees | Retrieve a pre-mapped institutional fee calendar | Public / bank-signed |

All requests and responses are JSON over HTTPS. Every write endpoint should accept an Idempotency-Key header.

### POST /v1/commitments/lock

Creates a new commitment of a given type and returns an invite code for members to join.

Request:

```json
{
  "type": "rotating",
  "title": "Equipment Rotation — Cohort A",
  "vendor_id": "vnd_slot_ng_01",
  "contribution_amount": 3500,
  "contribution_frequency": "weekly",
  "cycles": 5,
  "members": ["usr_01", "usr_02", "usr_03", "usr_04", "usr_05"]
}
```

Response:

```json
{
  "commitment_id": "cmt_88a1f",
  "type": "rotating",
  "status": "pending_members",
  "invite_code": "SURA-7X2Q",
  "payout_schedule": [
    { "cycle": 1, "beneficiary_id": "usr_01", "amount": 17500 },
    { "cycle": 2, "beneficiary_id": "usr_02", "amount": 17500 }
  ]
}
```

### POST /v1/commitments/float

Requests a micro-advance against one or more pre-mapped institutional fees.

Request:

```json
{
  "student_id": "usr_2Kf9a",
  "institution_id": "inst_unilag",
  "fee_ids": ["fee_lab_204", "fee_examcard"],
  "repayment_plan": "daily"
}
```

Response:

```json
{
  "float_id": "flt_10cd2",
  "approved_amount": 8000,
  "daily_debit": 350,
  "status": "disbursed_to_institution"
}
```

### GET /v1/score/{user_id}

Returns a user's current score and the pillar-by-pillar breakdown behind it.

Response:

```json
{
  "user_id": "usr_2Kf9a",
  "score": 742,
  "breakdown": {
    "commitment_behaviour": 0.35,
    "repayment_behaviour": 0.25,
    "transaction_stability": 0.20,
    "institutional_verification": 0.12,
    "social_reliability": 0.08
  },
  "last_updated": "2026-09-01T10:15:00Z"
}
```

---

## 08. Recommended Technology Stack

Chosen for one constraint above all others: a working, demoable API by the pitch deadline.

| Layer | Choice | Why |
|---|---|---|
| Backend API | Python + FastAPI | Minimal boilerplate and live interactive API docs |
| Database | PostgreSQL | Relational integrity matters when the data represents money and commitments |
| ORM / migrations | SQLAlchemy + Alembic | Reviewable, reversible schema changes |
| Sura Score logic | Python rule engine | Explainable and auditable |
| Auth | JWT + simulated student-portal OTP | Enough to demonstrate verified identity without a full KYC stack |
| Frontend | Next.js + Tailwind CSS | Clean, modern, mobile-first frontend for the product surface |
| Design | Figma | Shared source of truth for the UI/UX role |
| Hosting (backend + DB) | Railway or Render | Fast path from push to public URL |
| Hosting (frontend) | Vercel | Easy preview deployments |
| Version control | GitHub | Small team, short timeline |

### Important note for this project

This repo is backend-first. The team building the frontend will work on a separate Next.js app if required, but the core product and API work remains in this backend repository.

---

## 09. Regulatory & Compliance Positioning

This section matters because a bank's legal or risk team will push back on the first draft.

### What Sura claims

- Sura provides behavioural underwriting on top of a bank's existing identity verification — it never replaces KYC/AML.
- Sura is non-custodial: funds move directly between the bank, the user's account, and the vendor/institution.
- Every score decision is auditable by design.

### Intended licensing pathway

- API / decisioning layer registers under the Open Banking regulatory framework.
- Credit itself is extended under the partner bank's own licence.
- Disclosure is built to the FCCPC Digital Lending Regulations standard from day one.

### Data protection posture

- Sura operates as a data processor under the partner bank's NDPA registration.
- Score inputs are minimised by design.
- Consent for score computation is captured explicitly when a user joins their first commitment.

### What Sura does not claim

- Does not replace a bank's statutory KYC/AML obligations.
- Does not claim a specific default rate as fact for the MVP.
- Does not use CGPA as a standalone risk multiplier.

---

## 10. Revenue Model

Two proven mechanisms, not a wishlist.

| Stream | Mechanism | Proven comparable |
|---|---|---|
| Transaction fees | Small percentage on every vendor-locked payout and every Float disbursement | Paystack / Flutterwave |
| API / platform licensing | Monthly platform fee per institution | Mono / Okra |
| Interest spread | Share of the small interest margin on Float advances | Standard bank-fintech revenue share |

The pitch to the bank is simple: every micro-contribution, every vendor payout, and every fee advance is a transaction on your rails.

---

## 11. Stress-Testing Sura

### The hard question

If everyone contributes and one person collects first, what stops them walking away after?

Answer: new members are only eligible for the last slot once at least one group member has history to anchor the order. If everyone is new, the group self-selects who goes first, with the first payout capped low.

### Other key objections

- How do you underwrite someone with zero history?
- Who builds the vendor network this depends on?
- Why wouldn't the bank just build this in-house?
- How does the 3% Float fee hold up against real default risk?
- Isn't this just an ajo app?

Sura answers these conditions explicitly and does not hide behind vague claims.

---

## 12. Team & Roles

Four roles, one shared build.

### Backend Engineer — Core Systems

Owns:
- database schema
- commitment state machine
- REST endpoints
- lock simulation and settlement logic
- deployment and environment config

### Backend Engineer — AI / ML & Reputation Engine

Owns:
- Sura Score algorithm
- score recalculation events
- payout-schedule logic
- missed-contribution handling

### Frontend Engineer

Owns:
- commitment creation flow
- redemption flow
- score dashboard
- real API integration

### UI/UX Designer & Pitch Lead

Owns:
- design system
- wireframes
- pitch deck
- demo script and judgement prep

### Shared responsibilities

- daily standup
- sprint checks
- all-team review of the demo script

---

## 13. Build Plan — Phases & Milestones

### Phase 1 — Foundation

Goal: lock the idea and the architecture.

Key deliverables:
- finalised schema
- wireframes for all core screens
- fee calendars for 2 institutions
- repo and environment setup

### Phase 2 — Sprint 1

Goal: backend and frontend skeletons exist and talk to each other.

Key deliverables:
- auth and commitment CRUD live
- database deployed
- frontend shell deployed and calling a real API

### Phase 3 — Sprint 2

Goal: Sura Lock works end-to-end.

Key deliverables:
- full commitment lifecycle demoable
- Sura Score v1 live

### Phase 4 — Sprint 3

Goal: Sura Float and the score dashboard work end-to-end.

Key deliverables:
- Float request → approval → simulated disbursement
- score dashboard wired to real data

### Phase 5 — Polish

Goal: survive a live demo and a hostile question.

Key deliverables:
- bug bash across both flows
- mock settlement finished
- deck and script rehearsed

### Phase 6 — Finale

Goal: deliver.

Key deliverables:
- final rehearsal
- submission package complete
- live pitch

### Milestone checklist

- Schema finalised and reviewed by all four roles
- A judge could open the frontend URL and see something real
- Sura Lock fully demoable without a single hard-coded value
- Sura Float fully demoable; score dashboard shows real breakdown data
- Full demo rehearsed twice, end-to-end, under five minutes

### What we're actually demoing

Live in the demo:
- one commitment type: rotating
- one institution's fee calendar for Float
- core Sura Score with real breakdown
- vendor lock against 2–3 real merchants

Roadmap, not built yet:
- collective & individual goal commitment types
- multi-institution fee coverage
- production bank settlement

---

## 14. Demo & Pitch Script

Five minutes, four beats. The story leads; the product proves it.

### 0:00 – 0:45 — The Hook

“I play guitar. I also write code. Both pay me in bursts, not salaries…”

### 0:45 – 2:30 — Live Demo

- Sura Lock: create a rotating equipment commitment, invite peers, show the vendor lock and payout schedule.
- Sura Float: pick an institution, auto-populate the fee calendar, float the fee, show direct-to-institution disbursement.
- Sura Score: show the score and the pillar breakdown.

### 2:30 – 3:30 — The Business

This isn't an app. It's an API. Any bank plugs in Sura and instantly offers structured group savings, fee micro-advances, and a reputation engine.

### 3:30 – 4:30 — The Scale

Our MVP demonstrates the full architecture with two institutional fee calendars and simulated vendor settlement.

### 4:30 – 5:00 — The Close

In Yoruba, Sura means patience. But patience without structure is just waiting. Sura gives patience a bank account.

---

## 15. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Team over-builds both modules in parallel | Enforce the Lock-first rule |
| A judge asks for a real pilot the team doesn't have | Be honest about the MVP scope |
| Live demo fails on stage | Pre-seed clean demo account; keep backup recording |
| Score algorithm looks arbitrary | Keep every weight documented and traceable |
| Frontend and backend integrate too late | Start API integration from Week 2 |
| Regulatory pushback on vendor-lock / disbursement | Lead with the non-custodial framing |

---

## Appendix A — Glossary

| Term | Meaning |
|---|---|
| Ajo / esusu | Traditional Nigerian rotating or accumulating group-savings arrangement |
| Sura | Yoruba for patience, perseverance, endurance |
| Sura Lock | The commitment module |
| Rotating commitment | A Sura Lock type where the pooled contribution rotates to a different member at each cycle |
| Collective goal commitment | A commitment where every contributor shares in one common objective |
| Individual goal commitment | A commitment with one named beneficiary |
| Sura Float | The institutional fee micro-advance module |
| Sura Score | The shared, rule-based reputation score |
| Commitment Engine | Internal system owning Sura Lock and Sura Float |
| Reputation Engine | Internal system owning Sura Score |
| Vendor-lock | Restricting a commitment's payout so it can only ever settle to one verified vendor |

---

## Appendix B — Core Data Schema (Sketch)

A starting point for the Backend role in Week 1 — not a final schema.

### Core tables

- users (id, name, institution_id, phone, verified_at)
- institutions (id, name, fee_calendar_json)
- fee_items (id, institution_id, name, amount, term)
- vendors (id, name, category, verified_at)
- commitments (id, creator_id, type, title, vendor_id, contribution_amount, frequency, cycles, status, created_at)
- commitment_members (commitment_id, user_id, role, joined_at)
- commitment_beneficiaries (commitment_id, cycle_number, user_id, payout_amount, status)
- contributions (id, commitment_id, user_id, amount, paid_at)
- floats (id, student_id, institution_id, fee_ids, approved_amount, daily_debit, status)
- score_history (id, user_id, score, breakdown_json, computed_at)

The commitment's type field determines how commitment_beneficiaries is populated — one row per member for a collective goal, one row total for an individual goal, or one row per cycle for a rotating commitment.

---

## Final note

This master document defines the full Sura vision. The actual hackathon MVP should remain narrow, honest, and demoable. The key rule is simple: build Sura Lock deeply first, then prove the same engine supports Sura Float and Sura Score without overstretching the team.
