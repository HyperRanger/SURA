# Clean PWA test identities

This is a separate, clean account set for manual PWA testing. It never creates
Locks, contributions, vouchers, redemptions, settlement records, Score history,
or risk flags. It does not replace the richer bank-demo data set.

## Before running it

Run it only after migration `0023_partner_links_payouts` has been deployed.
Use the Render **External Database URL** from your computer; never commit that
URL or any password.

Choose three demo-only passwords locally. They are intentionally supplied at
runtime, not stored in source code or documentation:

```powershell
cd backend
$env:PWA_TEST_MEMBER_PASSWORD = "choose-a-member-demo-password"
$env:PWA_TEST_VENDOR_PASSWORD = "choose-a-vendor-demo-password"
$env:PWA_TEST_BANK_PASSWORD = "choose-a-bank-demo-password"
$env:DATABASE_URL = "<Render External Database URL>?sslmode=require"
python -m alembic upgrade head
python scripts/seed_pwa_test_identities.py --reset
Remove-Item Env:DATABASE_URL
Remove-Item Env:PWA_TEST_MEMBER_PASSWORD
Remove-Item Env:PWA_TEST_VENDOR_PASSWORD
Remove-Item Env:PWA_TEST_BANK_PASSWORD
```

`--reset` touches only identities owned by this script. It refuses to reset if
one of its members has acquired Lock activity, protecting test work from an
accidental delete.

For the isolated competition demo only, bank staff can either complete the
configured MFA flow or the Render demo environment can set
`BANK_MFA_REQUIRED=false`. Never disable bank MFA in a real deployment.

## Member accounts

All members use `PWA_TEST_MEMBER_PASSWORD`.

| Name | Context | Email | Phone |
|---|---|---|---|
| Ayo Adeyemi | student | member.01@pwa-test.sura.local | 08097000001 |
| Chiamaka Eze | student | member.02@pwa-test.sura.local | 08097000002 |
| Hauwa Bello | student | member.03@pwa-test.sura.local | 08097000003 |
| Kelechi Obi | student | member.04@pwa-test.sura.local | 08097000004 |
| Tolu Adebayo | student | member.05@pwa-test.sura.local | 08097000005 |
| Zainab Musa | student | member.06@pwa-test.sura.local | 08097000006 |
| Bisi Williams | trader | member.07@pwa-test.sura.local | 08097000007 |
| Emeka Okafor | trader | member.08@pwa-test.sura.local | 08097000008 |
| Favour Nwosu | trader | member.09@pwa-test.sura.local | 08097000009 |
| Ganiyu Afolabi | trader | member.10@pwa-test.sura.local | 08097000010 |
| Mfon Akpan | trader | member.11@pwa-test.sura.local | 08097000011 |
| Tari Briggs | trader | member.12@pwa-test.sura.local | 08097000012 |
| Damilola Grace | freelancer | member.13@pwa-test.sura.local | 08097000013 |
| Efe Oghene | freelancer | member.14@pwa-test.sura.local | 08097000014 |
| Ireti James | freelancer | member.15@pwa-test.sura.local | 08097000015 |
| Muna Adebayo | freelancer | member.16@pwa-test.sura.local | 08097000016 |
| Sadiq Ibrahim | freelancer | member.17@pwa-test.sura.local | 08097000017 |
| Adaeze Ibe | other | member.18@pwa-test.sura.local | 08097000018 |
| Boma Tamuno | other | member.19@pwa-test.sura.local | 08097000019 |
| Yejide Adewale | other | member.20@pwa-test.sura.local | 08097000020 |

## Vendor accounts

All vendors use `PWA_TEST_VENDOR_PASSWORD`. They are created verified and each
has five text-only catalogue items, but no redemption or settlement history.

| Business | Category | Email | Phone |
|---|---|---|---|
| Harmony Demo Music | music | vendor.01@pwa-test.sura.local | 08098000001 |
| Buildwell Demo Hardware | hardware | vendor.02@pwa-test.sura.local | 08098000002 |
| Market Basket Demo | groceries | vendor.03@pwa-test.sura.local | 08098000003 |
| Threadline Demo Fashion | fashion | vendor.04@pwa-test.sura.local | 08098000004 |
| Pocket Demo Mobile | mobile | vendor.05@pwa-test.sura.local | 08098000005 |
| Page One Demo Books | books | vendor.06@pwa-test.sura.local | 08098000006 |

## Bank Portal accounts

Each account is a `bank_admin` with the complete demo permission set and uses
`PWA_TEST_BANK_PASSWORD`. A member appears in one portal only after they choose
that bank under **Banks Sura supports** and explicitly consent to share their
Sura evidence. Selecting a source-bank name alone does nothing.

| Partner bank | Portal email |
|---|---|
| Orbit Bank | portal.admin@orbit.demo |
| Lantern Bank | portal.admin@lantern.demo |
| River Bank | portal.admin@river.demo |
