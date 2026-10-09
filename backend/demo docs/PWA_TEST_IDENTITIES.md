# Clean PWA test identities

This is a separate, clean account set for manual PWA testing. It never creates
Locks, contributions, vouchers, redemptions, settlement records, Score history,
or risk flags. It does not replace the richer bank-demo data set.

## Before running it

Run it only after migration `0024_goal_commitments` has been deployed.
Use the Render **External Database URL** from your computer; never commit that
URL or any password.

Use these public, demo-only credentials for the competition environment. Never
reuse them for a real account or production deployment:

```powershell
cd backend
$env:PWA_TEST_MEMBER_PASSWORD = "SuraMemberDemo26!"
$env:PWA_TEST_VENDOR_PASSWORD = "SuraVendorDemo26!"
$env:PWA_TEST_BANK_PASSWORD = "SuraBankDemo26!"
$env:DATABASE_URL = "PASTE_RENDER_EXTERNAL_DATABASE_URL_HERE"
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

Use Render's **External Database URL**, not its internal hostname. If the URL
you copy does not already include query parameters, append `?sslmode=require`.

Each account below has a deterministic, demo-only 10-digit account number.
The Link bank account screen displays the matching Sura name and accepts only
that account's own number; it stores only a masked number after linking. The
listed source bank is a suggested test label, not a real bank connection.

The existing account **Owolabi Olamilekan / 08106608598** is not seeded or
duplicated. Sign in and open **Profile → Link bank account** to see that
account's generated demo account number and matching holder name.

For the isolated competition demo only, bank staff can either complete the
configured MFA flow or the Render demo environment can set
`BANK_MFA_REQUIRED=false`. Never disable bank MFA in a real deployment.

## Member accounts

All members use `SuraMemberDemo26!`.

| Name / account holder | Type | Login email | Phone | Suggested source bank | Demo account number |
|---|---|---|---|---|---|
| Ayo Adeyemi | student | m01@sura.test | 08097000001 | GTBank | 2288268964 |
| Chiamaka Eze | student | m02@sura.test | 08097000002 | Kuda | 8705292524 |
| Hauwa Bello | student | m03@sura.test | 08097000003 | FirstBank | 1156360436 |
| Kelechi Obi | student | m04@sura.test | 08097000004 | UBA | 8149595088 |
| Tolu Adebayo | student | m05@sura.test | 08097000005 | Zenith Bank | 5656846492 |
| Zainab Musa | student | m06@sura.test | 08097000006 | Access Bank | 3823715826 |
| Bisi Williams | trader | m07@sura.test | 08097000007 | Moniepoint MFB | 4575111029 |
| Emeka Okafor | trader | m08@sura.test | 08097000008 | FCMB | 5878366753 |
| Favour Nwosu | trader | m09@sura.test | 08097000009 | Opay | 8651017898 |
| Ganiyu Afolabi | trader | m10@sura.test | 08097000010 | Wema Bank | 5995792562 |
| Mfon Akpan | trader | m11@sura.test | 08097000011 | Sterling Bank | 8314950028 |
| Tari Briggs | trader | m12@sura.test | 08097000012 | PalmPay | 7080727012 |
| Damilola Grace | freelancer | m13@sura.test | 08097000013 | Stanbic IBTC Bank | 2093030827 |
| Efe Oghene | freelancer | m14@sura.test | 08097000014 | Fidelity Bank | 2692692150 |
| Ireti James | freelancer | m15@sura.test | 08097000015 | Ecobank Nigeria | 7031362767 |
| Muna Adebayo | freelancer | m16@sura.test | 08097000016 | Union Bank | 3653752507 |
| Sadiq Ibrahim | freelancer | m17@sura.test | 08097000017 | Polaris Bank | 2561042166 |
| Adaeze Ibe | other | m18@sura.test | 08097000018 | Jaiz Bank | 8912236768 |
| Boma Tamuno | other | m19@sura.test | 08097000019 | Citibank Nigeria | 9954490156 |
| Yejide Adewale | other | m20@sura.test | 08097000020 | Orbit Bank | 5320701582 |

## Vendor accounts

All vendors use `SuraVendorDemo26!`. They are created verified and each
has five text-only catalogue items, but no redemption or settlement history.

| Business / account holder | Category | Login email | Phone | Suggested payout bank | Demo account number |
|---|---|---|---|---|---|
| Harmony Demo Music | music | v01@sura.test | 08098000001 | GTBank | 8058045488 |
| Buildwell Demo Hardware | hardware | v02@sura.test | 08098000002 | Access Bank | 9969973404 |
| Market Basket Demo | groceries | v03@sura.test | 08098000003 | FirstBank | 6041981313 |
| Threadline Demo Fashion | fashion | v04@sura.test | 08098000004 | Zenith Bank | 4294207095 |
| Pocket Demo Mobile | mobile | v05@sura.test | 08098000005 | Moniepoint MFB | 6344408096 |
| Page One Demo Books | books | v06@sura.test | 08098000006 | UBA | 1734020984 |

## Bank Portal accounts

Each account is a `bank_admin` with the complete demo permission set and uses
`SuraBankDemo26!`. A member appears in one portal only after they choose
that bank under **Banks Sura supports** and explicitly consent to share their
Sura evidence. Selecting a source-bank name alone does nothing.

| Partner bank | Portal email | Password |
|---|---|---|
| Orbit Bank | portal.admin@orbit.demo | SuraBankDemo26! |
| Lantern Bank | portal.admin@lantern.demo | SuraBankDemo26! |
| River Bank | portal.admin@river.demo | SuraBankDemo26! |
