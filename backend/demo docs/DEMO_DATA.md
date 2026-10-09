# Sura backend demo data

Run this only after Alembic migrations:

```powershell
cd backend
python scripts/seed_demo_data.py --reset
```

The command replaces only records with fixed Sura demo IDs. It does not clear
unrelated records.

## Population

The seed creates 90 fictional individual identities for **one** Sura API
partner: Sura Partner Bank (`bnk_sura_partner`). Its sole portal administrator
can search and review all 90 customers. The six banks below are the source
institutions members use; they are not separate Sura Portal tenants.

Customers deliberately vary by onboarding context, available balance, activity
cadence, Score-processing consent, account-review state, and Lock membership.
This supports realistic search, filters, empty states, portfolio views, and
Score scenarios without representing real people, banks, or balances.

The original 70-member Lock cohort is supplemented by 20 named customer
profiles across student, trader, freelancer, and other contexts. There are
still exactly 12 varied review flags across the complete portfolio. The
`GET /v1/bank/overview` response derives a deterministic simulated customer
balance snapshot of **₦10,405,933,000** from those individual records. It is
bank-owned demo context only—not Sura-held money, deposits, or an AUM claim.

| Source institution | ID | Customers |
|---|---|---:|
| Banter Bank | `inst_banter` | 16 |
| Chai Bank | `inst_chai` | 14 |
| Kolo Bank | `inst_kolo` | 12 |
| Jollof Bank | `inst_jollof` | 10 |
| Gbedu Bank | `inst_gbedu` | 10 |
| Sapa Bank | `inst_sapa` | 8 |

Names include modern English/Yoruba names, plus Igbo, Hausa, and other Nigerian
ethnicities. Every identity has a name. Account balances are integer NGN
snapshots available only to the Bank Portal, never to member or vendor APIs.

## Lock and review portfolio

- 25 rotating Locks: 10 active, 7 awaiting members, and 8 completed.
- Membership overlaps intentionally, so some members appear in more than one
  group and all 90 people can appear in realistic portfolio searches.
- Completed cycles have voucher and simulated vendor-redemption history.
- 12 varied review flags at most, with open, confirmed, dismissed, and
  escalated states. They are demo review records, not a claim that Sura has
  independently detected or verified fraud.

## Main Lock story

| Item | Demo value |
|---|---|
| Members | Amara Okafor and Tunde Adeyemi |
| Commitment | `cmt_demo_laptop_rotation` - Laptop Fund demo rotation |
| Vendor | Sura Demo Electronics (`vnd_demo_electronics`) |
| Cycle 1 | Fully contributed, settled to the vendor, and redeemed by Amara |
| Voucher | `SURA-DEMO-LAPTOP-01` |
| Cycle 2 | Active; Amara has paid and Tunde is outstanding |

## Sim Bank customer

The Sim_eco_bank walkthrough should use **Chiamaka Obiora**
(`usr_demo_portfolio_01`). Retrieve the profile through the existing machine
endpoint rather than copying identity or balance values into the bank UI:

```text
GET /v1/integrations/customers/usr_demo_portfolio_01
```

It requires an API key with `score:read`. The response contains the tenant-safe
customer name, score summary, active Lock counts, and simulated bank-owned
available-balance snapshot. The PWA test identities are not copied into this
portfolio: they become visible to a portal only when their owner explicitly
selects a Sura-supported partner bank and grants consent.

## Bank Portal login

Only one Bank Portal account is seeded. It uses the administrator role, which
has every portal permission for Sura Partner Bank. The password is demo-only; MFA is
still required.

| Role | Email |
|---|---|
| Bank Portal administrator | `demo.admin@sura.local` |

The demo password is `demo-password-never-in-production`. An OTP is returned
only outside production or delivered by configured Termii SMS.

## Useful endpoints

```text
GET /v1/commitments/cmt_demo_laptop_rotation
GET /v1/score/usr_demo_amara
GET /v1/score/usr_demo_tunde
GET /v1/vendors
GET /v1/bank/overview
GET /v1/bank/users?bank_customer_id=CUST-DEMO-8241
```

For a non-production bank shortcut, call `POST /v1/bank/demo-login`. It issues
a bank-administrator session for the primary demo tenant and is disabled in
production.

## Member authentication and contribution retries

```text
POST /v1/auth/demo-token
{"user_id":"usr_demo_amara","otp_code":"<DEMO_OTP_CODE>"}
```

Send the resulting access token as a bearer token to protected Lock routes. A
contribution requires a client-generated `event_id`; reuse it only for a retry
of the same payment. A matching replay returns `idempotent_replay: true`, while
the same ID with a different amount is rejected.
