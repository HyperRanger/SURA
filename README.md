# Sura

Sura is an infrastructure product for structured financial commitments, built for people whose income does not arrive as a monthly salary.

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
│   ├── core/
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── ...
├── docs/
│   ├── PRD.md
│   ├── TRD.md
│   ├── BUILD_PLAN.md
│   └── ...
├── .gitignore
└── ...
```

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
- [docs/PRD.md](docs/PRD.md)
- [docs/TRD.md](docs/TRD.md)
- [docs/BUILD_PLAN.md](docs/BUILD_PLAN.md)

## Team context

This project is designed for a four-person team split across:
- Backend Engineering
- AI / ML Engineering
- Frontend Engineering
- UI / UX & Pitch

The backend team owns the source of truth for the underlying system contract, while the frontend and design teams integrate against the production-ready API surface as it is built.

## Summary

Sura is a real-world financial infrastructure concept built around commitment, trust, and transparent decisioning. This repository captures the full product vision and the backend engineering execution path required to turn that vision into a working, demoable system.

The project is intentionally structured so the backend is strong, well-documented, and deployment-ready before any frontend layer is layered on top.
