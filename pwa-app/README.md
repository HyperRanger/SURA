# Sura member and vendor app

The mobile-first app where individual members run Sura Locks and vendors redeem vouchers.
It is its own Next.js project, separate from the marketing website and bank console in the
parent folder, with its own theme. The screens are specified in
[MEMBER_VENDOR_APP_SCREENS.md](./MEMBER_VENDOR_APP_SCREENS.md).

## Getting started

```bash
npm install
npm run dev   # http://localhost:4322
```

Create a `.env.local` with:

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_API_URL` | The Sura API, e.g. `http://localhost:8000` |
| `NEXT_PUBLIC_APP_ENV` | `development`, `staging` or `production`. Demo sign-ins and code hints are off in production |
| `NEXT_PUBLIC_DEMO_OTP_CODE` | The backend's `DEMO_OTP_CODE`, to sign in as the named seeded people on `/demo`. Never set in production |
| `NEXT_PUBLIC_SITE_URL` | The marketing website, e.g. `http://localhost:4321`, for the bank information page and the bank console |

## What's built

| Screen | Route |
|---|---|
| P1 Landing | `/` |
| P2 Sign up | `/signup` (`?role=vendor` skips the account question) |
| P3 Login | `/login` |
| P4 OTP verification | `/verify` |
| P5/P6 Terms and privacy | `/terms`, `/privacy` |
| P8 Demo switcher | `/demo` (not found in production) |

After verifying, members land on `/app` (or `/app/welcome` for a new account) and vendors on
`/vendor`, using the role from the API's token. Those areas are next.

## Theme

Same design language as the website (Nunito, raised cards, chunky buttons), with its own
palette in `app/globals.css`: iris leads on a cool lilac mist, marigold marks money and
payouts, and mint marks anything paid, confirmed or redeemed.

## Offline and install behaviour

The PWA registers a service worker after the first page load. It caches only the
public landing shell and same-origin static assets, allowing the installed app to
reopen to a safe offline screen when there is no connection.

It deliberately does **not** cache API responses, authentication tokens, OTPs,
vouchers, account data, scores, Locks, or any write request. Contributions,
redemption, and every financial action require an active connection.

On an HTTPS deployment, Android browsers can offer **Install app**. On iPhone,
open the app in Safari, tap **Share**, then choose **Add to Home Screen**.
