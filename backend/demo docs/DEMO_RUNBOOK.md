# Sura Lock and Score demo runbook

This is the repeatable backend story for the demo. It uses seeded data and a
simulated settlement; it does not claim a real transfer or Sura Float.

## Prepare the environment

1. Deploy a build whose migrations have completed.
2. Seed the selected demo database:

   ```powershell
   cd backend
   python scripts/seed_demo_data.py --reset
   ```

3. Confirm `GET /health` and open `/docs` on the deployed API.

The reset replaces only fixed demo records. It leaves unrelated data in place.

## 1. Members: a real rotating Lock

Use `GET /v1/commitments/cmt_demo_laptop_rotation`.

Show the Laptop Fund rotation: Amara and Tunde each contribute 5,000 weekly.
Cycle 1 is complete; Cycle 2 is active. Amara has paid Cycle 2 and Tunde is
outstanding. The payout order is fixed and visible in the commitment.

## 2. Vendor: funds remain vendor-locked

Use `SURA-DEMO-LAPTOP-01` with verified vendor `vnd_demo_electronics`.

Cycle 1 settled to Sura Demo Electronics and was redeemed by Amara. The seeded
voucher is already redeemed, so it is settlement evidence only. For an
interactive wrong-vendor rejection, create a fresh test commitment and voucher;
do not reuse the redeemed voucher.

## 3. Bank: one tenant sees its own portfolio

Sign in with the sole seeded portal account:

```text
email: demo.admin@sura.local
password: demo-password-never-in-production
```

Complete the MFA challenge from `POST /v1/bank/login`, then use its access token:

```text
GET /v1/bank/overview
GET /v1/bank/users?bank_customer_id=CUST-DEMO-8241
GET /v1/bank/users/usr_demo_amara/score
GET /v1/bank/commitments
GET /v1/bank/commitments/cmt_demo_laptop_rotation/group-health
GET /v1/bank/settlements
GET /v1/bank/audit-log
```

Banter Bank sees its 20-customer portfolio, including the Lock, advisory Group
Health, simulated settlement, Score history, and audit trail. The seed holds 70
customers across six tenants, allowing tenant-isolation and filter scenarios.
Bank staff records are excluded from customer counts.

## 4. Explain the score plainly

Use `GET /v1/score/usr_demo_amara` or the bank score route. Sura Score is a
deterministic, explainable rule-based score from observable Lock history. It is
not an AI decision and is not a credit-bureau score.

## Recovery

If a demo record changes, rerun the seed with `--reset`, then repeat the health
check. Retain a screen recording of a clean run as the presentation fallback.
