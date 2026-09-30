# Sura backend demo data

Run this only after Alembic migrations:

```powershell
cd backend
python scripts/seed_demo_data.py --reset
```

The command only replaces records with the fixed `demo` IDs; it does not clear real records.

For the ordered four-perspective walkthrough, use [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md).

| Item | Demo value |
|---|---|
| Members | Amara Okafor and Tunde Adeyemi |
| Bank tenant | `bnk_demo` — Demo Bank |
| Commitment | `cmt_demo_laptop_rotation` — Laptop Fund — Demo Rotation |
| Vendor | Sura Demo Electronics (`vnd_demo_electronics`) |
| Cycle 1 | Fully contributed, settled to the vendor, and redeemed by Amara |
| Voucher | `SURA-DEMO-LAPTOP-01` |
| Cycle 2 | Active; Amara has paid, Tunde is outstanding |

The seed also creates Bank Portal staff accounts. They use the demo-only password `demo-password-never-in-production`. Bank login then requires an OTP returned only outside production or delivered through configured Termii SMS.

| Role | Email |
|---|---|
| Bank administrator | `demo.admin@sura.local` |
| Risk analyst | `demo.risk@sura.local` |
| Integration engineer | `demo.integration@sura.local` |

The frontend can retrieve the full story from:

```text
GET /v1/commitments/cmt_demo_laptop_rotation
GET /v1/score/usr_demo_amara
GET /v1/score/usr_demo_tunde
GET /v1/vendors
GET /v1/bank/overview
GET /v1/bank/users?bank_customer_id=CUST-DEMO-8241
```

For a non-production bank shortcut, call `POST /v1/bank/demo-login`. It returns a risk-analyst session for `bnk_demo` and is disabled when `ENVIRONMENT=production`.

## Online demo authentication and contribution retries

Get a demo user token before calling protected Lock routes:

```text
POST /v1/auth/demo-token
{"user_id":"usr_demo_amara","otp_code":"<DEMO_OTP_CODE>"}
```

Send the returned value as `Authorization: Bearer <access_token>` to protected Lock routes.
Every contribution requires a client-generated `event_id` (normally a UUID). Reuse it only
when retrying that exact payment. A replay returns `"idempotent_replay": true`; reuse with a
different amount is rejected.
