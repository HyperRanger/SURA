# Sura Lock and Score demo runbook

This is the repeatable backend story for the October demo. It uses seeded data
and simulated settlement. It does not claim a real transfer or Sura Float.

## Prepare the environment

1. Deploy the build whose migrations have completed.
2. Run the seed once against the selected demo database:

   ```powershell
   cd backend
   python scripts/seed_demo_data.py --reset
   ```

3. Check `GET /health` and open `/docs` on the deployed API.

The reset only replaces records with fixed demo IDs. It leaves non-demo data in
place.

## The story to show

### 1. Members: a real rotating Lock

Use `GET /v1/commitments/cmt_demo_laptop_rotation`.

Show the Laptop Fund rotation: Amara and Tunde each contribute 5,000 per week.
Cycle 1 is complete and Cycle 2 is active. Amara has paid Cycle 2; Tunde is
still outstanding. The payout order is fixed and visible in the commitment.

### 2. Vendor: funds remain vendor-locked

Use the voucher `SURA-DEMO-LAPTOP-01` with the verified vendor
`vnd_demo_electronics`.

Show that Cycle 1 settled to Sura Demo Electronics and was redeemed by Amara.
The seeded voucher is already redeemed, so use it as settlement evidence only.
For an interactive wrong-vendor rejection, create a fresh test commitment and
voucher first; do not reuse the redeemed demo voucher.

### 3. Bank: the same events are visible to the institution

Sign in with the seeded risk analyst account:

```text
email: demo.risk@sura.local
password: demo-password-never-in-production
```

Complete the MFA challenge returned by `POST /v1/bank/login`, then use the
access token on these routes:

```text
GET /v1/bank/overview
GET /v1/bank/users?bank_customer_id=CUST-DEMO-8241
GET /v1/bank/users/usr_demo_amara/score
GET /v1/bank/commitments
GET /v1/bank/settlements
GET /v1/bank/audit-log
```

The bank sees two customers, the Lock commitment, the simulated settlement,
the score history, and the audit trail. Bank staff accounts are deliberately
excluded from customer search and customer counts.

### 4. Explain the score plainly

Use `GET /v1/score/usr_demo_amara` or the bank score route above. Explain that
Sura Score is a deterministic, explainable rule-based score from observable
Lock history. It is not an AI decision and it is not a credit-bureau score.

## Recovery

If any demo record was changed, rerun the seed command with `--reset` and repeat
the health check. Keep a screen recording of a clean run as the presentation
backup.
