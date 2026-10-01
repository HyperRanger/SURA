# Sura backend demo data

Run this only after Alembic migrations:

```powershell
cd backend
python scripts/seed_demo_data.py --reset
```

The command replaces only records with fixed Sura demo IDs. It does not clear
unrelated records.

## Population

The seed creates 70 individual customer identities across six sandbox bank
tenants. The customers deliberately vary by onboarding context, available
balance, activity cadence, Score-processing consent, and account-review state.
This supports realistic search, filter, empty-state, tenant-isolation, and
Score scenarios without representing real people or bank balances.

| Bank | ID | Customers |
|---|---|---:|
| Banter Bank | `bnk_banter` | 20 |
| Chai Bank | `bnk_chai` | 14 |
| Kolo Bank | `bnk_kolo` | 12 |
| Jollof Bank | `bnk_jollof` | 10 |
| Gbedu Bank | `bnk_gbedu` | 8 |
| Sapa Bank | `bnk_sapa` | 6 |

The primary Bank Portal tenant is Banter Bank. Its portfolio contains the
existing Lock walkthrough members, Amara Okafor and Tunde Adeyemi, plus 18
additional tenant-scoped customers. Account balances are stored as integer
NGN snapshots and are available only to the Bank Portal, never to member or
vendor APIs.

## Main Lock story

| Item | Demo value |
|---|---|
| Members | Amara Okafor and Tunde Adeyemi |
| Commitment | `cmt_demo_laptop_rotation` - Laptop Fund demo rotation |
| Vendor | Sura Demo Electronics (`vnd_demo_electronics`) |
| Cycle 1 | Fully contributed, settled to the vendor, and redeemed by Amara |
| Voucher | `SURA-DEMO-LAPTOP-01` |
| Cycle 2 | Active; Amara has paid and Tunde is outstanding |

## Bank Portal login

Only one Bank Portal account is seeded. It uses the administrator role, which
has every portal permission for Banter Bank. The password is demo-only; MFA is
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
