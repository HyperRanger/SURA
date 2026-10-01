# Backend Release and Demo Readiness

This is the release gate for the backend slice. It separates checks that can
run locally from actions that modify the deployed database or production branch.

## Local gate

Run these on the exact commit proposed for release:

```powershell
cd backend
python -m pytest tests -q
python -m alembic -c alembic.ini heads
```

Expected migration result: exactly one head, `0016_demo_balance`.

Confirm that `.env` is ignored and no secret appears in tracked files:

```powershell
git ls-files .env
git grep -n -I -e "postgresql://" -e "TERMII_API_KEY=" -e "SECRET_KEY=" -- ":!backend/.env.example"
```

## Deployment gate

1. Commit and push the approved `Backend` revision.
2. Merge the reviewed pull request into production `Master`.
3. Let Render deploy the exact merged commit and run `alembic upgrade head`.
4. Verify `GET /health`, `GET /docs`, and `GET /openapi.json` on the deployed
   API URL.
5. Confirm the OpenAPI document includes the intended PWA additions:
   - `/v1/app/recommendations/vendors`
   - `/v1/app/commitments/{commitment_id}/group-health`

Render service settings for this repository:

```text
Root directory: backend
Build command: pip install -r requirements.txt && alembic upgrade head
Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set `DATABASE_URL`, `SECRET_KEY`, JWT settings, and production Termii values in
Render environment variables. Never place any of them in the repository or in
the service commands.

## Demo database gate

After migrations are complete, seed only the selected demo database:

```powershell
cd backend
python scripts/seed_demo_data.py --reset
```

The reset replaces fixed demo IDs only; it does not wipe unrelated records.
Then follow [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md) and retain a clean screen
recording as a fallback.

## Honest demo boundary

- Lock contribution, voucher, redemption, and settlement records are tested
  backend flows, but settlement is simulated in this MVP.
- Score, Matching v1, and Group Health v1 are deterministic and explainable.
- Group Health and Matching are advisory: they do not make credit, fraud, or
  payment decisions.
- Sura Float is not part of this release.
