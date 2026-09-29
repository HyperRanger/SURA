# SURA

The infrastructure of commitment.

Sura is infrastructure for structured financial commitments, built for people whose income does not arrive as a monthly salary.

![Status](https://img.shields.io/badge/status-active%20build-D9A441)
![Python](https://img.shields.io/badge/python-3.11%2B-29235C)
![Framework](https://img.shields.io/badge/api-FastAPI-29235C)
![Database](https://img.shields.io/badge/database-PostgreSQL-29235C)
![Tests](https://img.shields.io/badge/score%20engine-16%20cases%20passing-D9A441)
![Scope](https://img.shields.io/badge/InnovateX-2026-171717)

Sura helps banks and fintechs offer a more transparent and more usable alternative to traditional salary based underwriting, by combining three modules on one API.

- Sura Lock, programmable commitment flows
- Sura Float, institutional fee micro-advance logic
- Sura Score, a transparent reputation engine

This repository is the project home for the full Sura vision, but the current implementation scope is deliberately backend first. The core product logic, API layer, schema design, scoring engine, and deployment ready backend structure live here.

## October 8 demo boundary

The live demo proves one rotating Sura Lock from four perspectives: members create and fund it, the matching vendor redeems its vendor-locked voucher, and the bank sees the same commitment, settlement, score movement, and audit evidence.

Sura Float is roadmap-only for this demo. Bank settlement and account-rail activity are simulated; Sura does not custody money, execute real transfers, replace the bank's lender-of-record role, or take ownership of the customer relationship.

## Contents

- Why Sura exists
- Product modules
- Architecture at a glance
- Build status
- Quick start
- Running the tests
- Project structure
- Current build intent
- Technology stack
- Project documents
- Team and ownership
- Contributing
- License

## Why Sura exists

Most Nigerians who work in the informal economy are excluded from traditional credit systems because they do not have a formal payslip, even when their financial behaviour is disciplined and consistent.

Sura addresses that gap by turning real behavioural data into a bank readable trust layer.

- Contribution history
- Commitment completion
- Vendor locked redemption
- Missed contribution handling
- Score evolution over time

## Product modules

### Sura Lock

A commitment engine for rotating, collective, and individual goal structures, where users contribute toward a specific outcome and the system enforces the rules. It never decides who benefits. It only enforces the terms a group already agreed to.

### Sura Float

A micro-advance mechanism for institutional fees or structured obligations, where repayment is enforced by a real authority such as a school, an institution, or a service provider.

### Sura Score

A transparent, rule based score that rewards consistency and completion, without hiding the logic behind a black box model.

#### How it is calculated

The score is a weighted sum across five pillars, not a trained model. Every point on it traces back to a named pillar and a named signal, which is what makes it auditable for a bank.

| Pillar | Weight | Signal |
|---|---|---|
| Commitment behaviour | 35% | Locks completed versus joined, and contributions paid on time |
| Repayment behaviour | 25% | Sura Float repayments made on time |
| Transaction stability | 20% | Regularity of account activity, measured as the coefficient of variation of the gaps between events |
| Institutional verification | 12% | Verified identity via student portal, trade association, or gig platform history |
| Social reliability | 8% | Peer co-signers from the same verified circle, capped at two |

Each pillar produces a sub-score between 0.0 and 1.0, which is multiplied by its weight and the 1000 point maximum. Sub-scores are rounded per pillar, so the breakdown shown to a user always sums exactly to the score they were given.

**Cold start.** A newly verified user with no commitment history scores exactly 120, because only the institutional verification pillar applies. That figure is derived from the weight rather than chosen by hand, and it is the anchor the rotating commitment ordering and cap rule compares against. This is deliberate. A score model with no honest answer for someone with zero history just rebuilds the exclusion it claims to fix.

#### Reference points

These are the numbers the test suite asserts, so a change to any weight or rule shows up as a failing test rather than a silently different score.

| User | Score |
|---|---|
| No history, unverified | 0 |
| No history, verified (entry tier) | 120 |
| One completed rotation, all contributions on time, regular activity, two co-signers | 750 |
| The same user after missing one of four contributions | 706 |
| Every pillar at maximum | 1000 |

## Architecture at a glance

```text
Client (web app, or the demo switcher for stage use)
        |
        v
FastAPI app (app/main.py)
        |
routers/     thin HTTP layer, no business logic
        |
services/    Commitment Engine and Reputation Engine, pure functions
        |
PostgreSQL   via SQLAlchemy models and Alembic migrations
```

`app/routers/` stays thin and does no decisioning of its own. Business rules live in `app/services/` as pure functions with no database, clock, or HTTP dependency, so any result can be reproduced directly from the events that produced it, and tested without spinning up the API.

## Build status

| Area | State |
|---|---|
| Sura Lock: consent, invite, contribution, payout, idempotency | Implemented and tested |
| Vendor verification, voucher issuance, and redemption | Implemented and tested |
| Sura Score 0–1000 and explainable score history | Implemented and tested |
| Bank Portal: tenant search, score audit, flags, and settlements | Implemented and tested |
| Developer Hub: scoped keys and machine score/commitment API; signed webhook test deliveries and logs | In progress; outbound event delivery worker remains |
| Sura Float | Roadmap only; intentionally not implemented for October 8 |

## Quick start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs once it is running. That live, interactive page is generated directly from the code, so it is worth showing to judges as proof the API is real, not a mock up.

## Running the tests

The score tests are pure Python and need nothing but pytest.

```bash
cd backend
python -m pytest app/tests/test_scoring.py -v
```

The full suite additionally needs `pip install -r requirements.txt` and a reachable database.

## Project structure

```text
Sura/
├── README.md
├── SURA_MASTER_BLUEPRINT.md
├── Sura-PRD.md
├── Sura-TRD.md
├── Sura-Build-Plan.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   ├── routers/        # HTTP layer, one module per resource
│   │   ├── services/       # business rules, pure and testable
│   │   └── tests/
│   ├── core/                # config, security, idempotency
│   ├── alembic/              # migrations
│   ├── scripts/
│   ├── requirements.txt
│   └── .env.example
└── .gitignore
```

## Current build intent

This repository is centered on the backend and API layer, because that is the technical foundation for the entire product.

The current implementation and design focus includes the following.

- API contracts for commitments, scoring, vendors, and settlement flows
- Database schema and relationship design
- Commitment lifecycle state tracking
- Score calculation logic and event driven updates
- Deployment friendly backend architecture
- Backend test coverage for critical business rules

Frontend implementation is not part of this repository's active build scope. The frontend is a separate delivery layer that integrates against the same API contract defined here.

## Technology stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- JWT with a demo OTP flow
- Railway or Render as the deployment target

## Project documents

The project documents are the source of truth for scope, architecture, technical requirements, build flow, and delivery milestones.

- SURA_MASTER_BLUEPRINT.md, the full product vision and pitch
- Sura-PRD.md, product requirements and regional demo scope
- Sura-TRD.md, technical requirements, including the anchor and cap rule
- Sura-Build-Plan.md, day by day tasks and ownership

Section 5.2 of the TRD is the scoring specification. It is the source of truth for the weights, the cold start baseline, and when a recalculation is triggered. This README summarises it. The TRD governs if the two ever disagree.

## Team and ownership

This project is built by a four person team.

| Role | GitHub | Owns |
|---|---|---|
| Backend Core | @HyperRanger | Schema, lock and contribute endpoints, the anchor and cap rule, vendor and redemption, deployment |
| Backend AI or ML | @Olatunji_Tobi | Sura Score rule engine, the score endpoint, score recalculation behaviour |
| Frontend Engineering | @fisayobadina | Create, join, contribute, redeem, and score dashboard screens, against the API contract |
| UI or UX and Pitch | unconfirmed | Design system, wireframes, slide deck, demo script |

The backend team owns the source of truth for the underlying system contract. The frontend and design teams integrate against the production ready API surface as it is built.

## Contributing

Everyone works on a feature branch off main and opens a pull request back into it. main stays deployable at all times.

Ownership rules that prevent duplicate work, from the build plan.

- One person owns the schema. That is Backend Core. Everyone else reads models.py. Nobody else edits it without telling Backend Core first.
- Frontend never guesses at what an API returns. If a response shape is not written down in Sura-TRD.md, ask Backend Core before writing code that assumes it.
- No task has two owners. If something is too big for one person, split it into two checklist items rather than putting both names on one.
- The daily fifteen minute sync is not optional. Most duplicate work happens because two people quietly built the same thing on the same day without saying so.

## License

Built for submission to InnovateX 2026. A license for use beyond the competition has not been decided yet. Until then, treat this repository as all rights reserved to its authors.

## Summary

Sura is a real world financial infrastructure concept, built around commitment, trust, and transparent decisioning. This repository captures the full product vision and the backend engineering execution path required to turn that vision into a working, demoable system.

The project is intentionally structured so the backend is strong, well documented, and deployment ready before any frontend layer is built on top of it.# SURA

Sura is an infrastructure product for structured financial commitments, built for people whose income does not arrive as a monthly salary.

## Brand direction

Tagline: The infrastructure of commitment.

Primary palette:
- Deep Indigo `#29235C` for the primary brand color and dominant product surfaces
- Gold `#D9A441` for completed commitments, score highlights, locked funds, and success states
- Ivory `#F7F5EF` for the background so the product feels warm and distinct from a corporate banking dashboard
- Near Black `#171717` for text and high-contrast UI copy

Sura helps banks and fintechs offer a more transparent and more usable alternative to traditional salary-based underwriting by combining:
- Sura Lock: programmable commitment flows
- Sura Float: institutional fee micro-advance logic
- Sura Score: a transparent reputation engine

This repository is the project home for the full Sura vision, but the current implementation scope is deliberately backend-first. The core product logic, API layer, schema design, scoring engine, and deployment-ready backend structure live here.

## Why Sura exists

Most Nigerians who work in the informal economy are excluded from traditional credit systems because they do not have a formal payslip, even when their financial behaviour is disciplined and consistent.

Sura addresses that gap by turning real behavioural data into a bank-readable trust layer:
- contribution history
- commitment completion
- vendor-locked redemption
- missed contribution handling
- score evolution over time

## Product modules

### Sura Lock
A commitment engine for rotating, collective, and individual goal structures where users contribute toward a specific outcome and the system enforces the rules.

### Sura Float
A micro-advance mechanism for institutional fees or structured obligations where repayment is enforced by a real authority such as a school, institution, or service provider.

### Sura Score
A transparent, rule-based score that rewards consistency and completion without hiding the logic behind a black-box model.

#### How it is calculated
The score is a weighted sum across five pillars, not a trained model. Every point on it traces back to a named pillar and a named signal, which is what makes it auditable for a bank.

| Pillar | Weight | Signal |
|---|---|---|
| Commitment behaviour | 35% | Locks completed vs joined, and contributions paid on time |
| Repayment behaviour | 25% | Sura Float repayments made on time |
| Transaction stability | 20% | Regularity of account activity, measured as coefficient of variation of the gaps between events |
| Institutional verification | 12% | Verified identity via student portal, trade association, or gig platform history |
| Social reliability | 8% | Peer co-signers from the same verified circle, capped at two |

Each pillar produces a sub-score between 0.0 and 1.0, which is multiplied by its weight and the 1000-point maximum. Sub-scores are rounded per pillar, so the breakdown shown to a user always sums exactly to the score they were given.

**Cold start.** A newly verified user with no commitment history scores exactly 120, because only the institutional verification pillar applies. That figure is derived from the weight rather than chosen by hand, and it is the anchor the rotating-commitment ordering and cap rule compares against. This is deliberate: a score model with no honest answer for someone with zero history just rebuilds the exclusion it claims to fix.

#### Reference points
These are the numbers the test suite asserts, so a change to any weight or rule shows up as a failing test rather than a silently different score.

| User | Score |
|---|---|
| No history, unverified | 0 |
| No history, verified (entry tier) | 120 |
| One completed rotation, all contributions on time, regular activity, two co-signers | 750 |
| The same user after missing one of four contributions | 706 |
| Every pillar at maximum | 1000 |

## Build status

| Area | State |
|---|---|
| Sura Lock: consent, invite, contribution, payout, idempotency | Implemented and tested |
| Vendor verification, voucher issuance, and redemption | Implemented and tested |
| Sura Score 0–1000 and explainable score history | Implemented and tested |
| Bank Portal: tenant search, score audit, flags, and settlements | Implemented and tested |
| Developer Hub: scoped keys and machine score/commitment API; signed webhook test deliveries and logs | In progress; outbound event delivery worker remains |
| Sura Float | Roadmap only; intentionally not implemented for October 8 |

The score endpoint is driven by real Lock events. The demo must show score changes caused by the live commitment flow, not a hardcoded value.

## Running the tests

The score tests are pure Python and need nothing but pytest:

```bash
cd backend
python -m pytest app/tests/test_scoring.py -v
```

The full suite additionally needs `pip install -r requirements.txt` and a reachable database.

## Project structure

```text
Sura/
├── README.md
├── SURA_MASTER_BLUEPRINT.md
├── Sura-PRD.md
├── Sura-TRD.md
├── Sura-Build-Plan.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   ├── routers/        # HTTP layer, one module per resource
│   │   ├── services/       # business rules, pure and testable
│   │   └── tests/
│   ├── core/               # config, security, idempotency
│   ├── alembic/            # migrations
│   ├── scripts/
│   ├── requirements.txt
│   └── .env.example
└── .gitignore
```

Business rules live in `app/services/` and are written as pure functions with no database, clock, or HTTP dependency, so they can be tested directly and any result can be reproduced from the events that produced it. `app/routers/` stays thin and does no decisioning of its own.

## Current build intent

This repo is centered on the backend and API layer because that is the technical foundation for the entire product.

The current implementation and design focus includes:
- API contracts for commitments, scoring, vendors, and settlement flows
- database schema and relationship design
- commitment lifecycle state tracking
- score calculation logic and event-driven updates
- deployment-friendly backend architecture
- backend test coverage for critical business rules

Frontend implementation is not treated as part of this repository's active build scope. The frontend will be a separate delivery layer that integrates against the same API contract defined here.

## Technology stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- JWT + demo OTP flow
- Railway / Render deployment target

## Backend quick start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

## API and project documents

The project documents are the source of truth for scope, architecture, technical requirements, build flow, and delivery milestones.

- [SURA_MASTER_BLUEPRINT.md](SURA_MASTER_BLUEPRINT.md)
- [Sura-PRD.md](Sura-PRD.md)
- [Sura-TRD.md](Sura-TRD.md)
- [Sura-Build-Plan.md](Sura-Build-Plan.md)

Section 5.2 of the TRD is the scoring specification. It is the source of truth for the weights, the cold-start baseline, and when a recalculation is triggered.

## Team context

This project is designed for a four-person team split across:

| Role | GitHub | Owns |
|---|---|---|
| Backend Core | _unconfirmed_ | Schema, lock and contribute endpoints, anchor and cap rule, vendor and redemption, deployment |
| Backend AI / ML | @Olatunji_Tobi | Sura Score rule engine, score endpoint, score recalculation behaviour |
| Frontend Engineering | @fisayobadina | Create, join, contribute, redeem, and score dashboard screens against the API contract |
| UI / UX & Pitch | _unconfirmed_ | Design system, wireframes, slide deck, demo script |

The backend team owns the source of truth for the underlying system contract, while the frontend and design teams integrate against the production-ready API surface as it is built.

Ownership rules that prevent duplicate work, from the build plan:
- One person owns the schema. That is Backend Core. Everyone else reads `models.py`; nobody else edits it without telling Backend Core first.
- Frontend never guesses at what an API returns. If a response shape is not written down in `Sura-TRD.md`, ask Backend Core before writing code that assumes it.
- No task has two owners. If something is too big for one person, split it into two checklist items rather than putting both names on one.
- The daily 15-minute sync is not optional. Most duplicate work happens because two people quietly built the same thing on the same day without saying so.

## Summary

Sura is a real-world financial infrastructure concept built around commitment, trust, and transparent decisioning. This repository captures the full product vision and the backend engineering execution path required to turn that vision into a working, demoable system.

The project is intentionally structured so the backend is strong, well-documented, and deployment-ready before any frontend layer is layered on top.
