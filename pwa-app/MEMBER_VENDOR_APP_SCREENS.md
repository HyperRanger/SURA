# Sura Member and Vendor App — Screen Specification

## Purpose

This is one mobile-first Sura application with role-based areas. Individual members use it to create and complete Sura Lock commitments. Vendors use the same product to securely validate and confirm vendor-locked vouchers.

The primary individual contexts are student, trader, freelancer, and other. They personalise onboarding and future verification; they do **not** grant different permissions. Vendor is a distinct role because it can access the merchant terminal and settlement history.

## Registration and routing

```text
Sign up
├── Individual
│   └── Context: Student / Trader / Freelancer / Other
│       └── /app/*
└── Vendor
    └── Business identity and verification
        └── /vendor/*
```

The role must be assigned by the backend, placed in the authenticated session/token, and checked again by every protected backend endpoint. The frontend route alone must never be treated as authorisation.

## Shared product rules

- Mobile first: design for a 390px-wide viewport; desktop is an enhanced layout.
- Every data screen has loading, empty, error/retry, and populated states.
- Use whole-naira amounts only and format money as `₦17,500`.
- A member never sees another member's Sura Score.
- A vendor sees the beneficiary's first name only, never their phone number or score.
- A contribution action disables after first tap and submits a stable retry identifier. A retry must display `Already recorded`, never create a duplicate contribution.
- Three vendor-locked commitment types are available: Rotating Sura Lock, Collective goal, and Individual goal. All contribute toward a declared target or cycle pool and release a voucher only to the verified vendor; none creates a cash-withdrawal route.

## App navigation

```text
/                         Landing page
/signup                   Select Individual or Vendor, then account details
/login                    Sign in
/verify                   OTP verification
/demo                     Demo-role switcher; non-production only
/terms  /privacy           Static policy pages

/app                      Member home
  /welcome
  /commitments
    /new
    /:id
      /contribute
      /contribute/receipt
      /cycles/:cycle/voucher
  /join
    /:code
    /:code/done
  /consent
  /score
    /history
      /:entry_id
    /how-it-works
  /float
  /notifications
  /profile
    /verification
    /privacy
    /settings
  /help
  /account-review

/vendor
  /login
  /
  /redeem
  /redeem/review
  /redeem/success
  /redeem/rejected
  /history
  /history/:redemption_id
```

## Public and account screens

### P1 — Landing

**Route:** `/`

- Sura's problem, Lock explanation, vendor lock, Score explanation, and calls to action.
- Links to sign up, login, try demo, terms, privacy, and the bank-information page.

### P2 — Sign up

**Route:** `/signup`

- First choice: `Individual` or `Vendor`.
- Individual: full name, phone, income context (student/trader/freelancer/other), terms acceptance.
- Vendor: business name, category, contact, and verification-onboarding state.
- Routes to OTP verification.

### P3 — Login

**Route:** `/login`

- Phone or supported identity input and continue button.
- Routes to OTP verification.

### P4 — OTP verification

**Route:** `/verify`

- Six-digit code, resend timer, and demo-code hint in non-production only.
- Individual routes to member home; vendor routes to vendor terminal.

### P5/P6 — Terms and privacy

**Routes:** `/terms`, `/privacy`

- Terms of use and privacy/score-processing information.

### P8 — Demo switcher

**Route:** `/demo`

- One-tap switch into seeded individual, vendor, and bank demo roles.
- Must be disabled or unavailable in production.

## Member screens

The member bottom navigation is Home, Commitments, Score, and Profile. The wizard and voucher use focused layouts without the bottom navigation.

### M1 — Home

**Route:** `/app`

- Greeting, private score chip, active commitment summary, next payout card, create/join actions, and warning banners.

### M2 — Welcome

**Route:** `/app/welcome`

- Short explanation of commitments, vendor lock, and Sura Score for a first-time member.

### M3 — My commitments

**Route:** `/app/commitments`

- Active, pending, and completed tabs.
- Each item shows title, status, progress, and next event.
- Empty state gives Create and Join actions.

### M4 — Create Sura Lock wizard

**Route:** `/app/commitments/new`

The state survives refresh. The frontend displays policy decisions returned by the backend; it does not calculate payout order or safety caps itself.

| Step | Content |
|---|---|
| M4a: Basics | Title and commitment type cards: rotating Lock, collective goal, and individual goal. |
| M4b: Vendor | Verified-vendor picker showing name, category, and verification badge. Vendor becomes locked after creation. |
| M4c: Contribution | Amount and daily/weekly/monthly frequency. Rotating Locks show cycles and a pool-per-cycle preview; goal commitments require a declared target amount. |
| M4d: Members | Add by phone or share invite code; show required/confirmed count. |
| M4e: Members and beneficiary | Rotating Locks use the backend payout order and explain the first-payout cap. Collective goals invite at least one other member and nominate the single voucher beneficiary. Individual goals have no additional members and the creator is the beneficiary. |
| M4f: Review | Full summary, payout schedule, cap notice, and confirm action. |
| M4g: Success | Invite code with copy/share actions; pending-members state and detail link. |

### M5 — Join by invite

**Route:** `/app/join`

- Invite-code field, join action, invalid/expired/full-commitment errors.

### M6 — Invite preview

**Route:** `/app/join/:code`

- Title, vendor, contribution amount/frequency, cycles, current members, member's proposed payout slot, and schedule.
- Routes through consent where required.

### M7 — Score-processing consent

**Route:** `/app/consent`

- Plain-language explanation of stored data, score purpose, and limits.
- Agree/decline actions. Required before first create or join.

### M8 — Joined confirmation

**Route:** `/app/join/:code/done`

- Confirmation, joined members, what happens next, and detail link.

### M9 — Commitment detail hub

**Route:** `/app/commitments/:id`

- Pinned action changes with the state: Contribute, Show voucher, Share invite, or no action.
- Pending state shows the invite code, member count, sharing action, and cancellation option where eligible.

| Tab | Content |
|---|---|
| Overview | Status, cycle progress, who has paid, next payout, beneficiary, pinned action. |
| Schedule | Each cycle's beneficiary, amount, date, status: scheduled, paid, redeemed. Highlight the member's own row. |
| Members | Name, role, current-cycle paid/not paid, missed count. Never show scores. |
| Activity | Created, joined, contributed, cycle completed, voucher issued, redeemed. |

### M10 — Contribute

**Route:** `/app/commitments/:id/contribute`

- Current cycle, locked amount due, current contribution progress, confirm button.
- Creates/reuses a stable client event ID for retry safety.

### M11 — Contribution receipt

**Route:** `/app/commitments/:id/contribute/receipt`

- Success reference, updated progress, and return link.
- Retry state explicitly says `Already recorded`.

### M12/M13 — Voucher and redeemed state

**Route:** `/app/commitments/:id/cycles/:cycle/voucher`

- Only the beneficiary can access it.
- Vendor name, locked amount, voucher code/QR, expiry, and status.
- States: locked, ready, redeemed, expired.
- The screen refreshes after vendor confirmation and becomes the M13 redeemed state with vendor and time.

### M14 — Cancel pending commitment

**Presentation:** confirmation modal from M9.

- Available only while the commitment remains pending under the backend policy.

### M15 — Missed contribution notice

**Presentation:** sheet from M1/M9.

- Explains missed state, score impact, recovery/eligibility policy, and next action.

### M16 — Sura Score

**Route:** `/app/score`

- Private score dial, tier, five pillars, next-unlock explanation, history link, and Float eligibility.

### M17/M18 — Score history and detail

**Routes:** `/app/score/history`, `/app/score/history/:entry_id`

- Filterable score-event log and explainable score-change detail: before, after, pillar, event, inputs, and rule.

### M19 — How score works

**Route:** `/app/score/how-it-works`

- Five weights, data sources, cold-start rules, and what the score is not.

### M20 — Float teaser

**Route:** `/app/float`

- Clearly locked teaser until Float is built and the user becomes eligible. No request form in the Lock demo.

### M21–M27 — Account and support

| Route | Purpose |
|---|---|
| `/app/notifications` | Contribution due, cycle complete, voucher ready, and flag notifications. |
| `/app/profile` | Name, phone, tier, logout, and profile links. |
| `/app/profile/verification` | Verification state and score relevance. |
| `/app/profile/privacy` | Data use, consent, and consent withdrawal. |
| `/app/profile/settings` | Notification preferences and logout. |
| `/app/help` | FAQ and support. |
| `/app/account-review` | Restricted-account explanation and help path after a fraud flag. |

## Vendor screens

The vendor area is intentionally minimal, high contrast, and usable while standing behind a counter.

### V1 — Vendor login

**Route:** `/vendor/login`

- Vendor code and PIN or approved vendor authentication.
- Demo bypass only in the demo environment.

### V2 — Vendor dashboard

**Route:** `/vendor`

- Large Redeem voucher action, today's settled total, and recent redemptions.

### V3 — Voucher input/scanner

**Route:** `/vendor/redeem`

- Manual voucher-code entry and optional camera QR scan.

### V4 — Redemption review

**Route:** `/vendor/redeem/review`

- Beneficiary first name only, commitment title, cycle, amount, and confirm/reject handover actions.
- Backend validates that this vendor is the vendor locked on the voucher.

### V5 — Redemption success

**Route:** `/vendor/redeem/success`

- Receipt, amount, timestamp, settlement reference, and clear simulated-settlement note for MVP.

### V6 — Redemption rejected

**Route:** `/vendor/redeem/rejected`

- Explicit reason: wrong vendor, voucher already redeemed, voucher expired, or invalid code.
- This is a key live-demo proof of vendor lock.

### V7/V8 — Redemption history

**Routes:** `/vendor/history`, `/vendor/history/:redemption_id`

- Historical redemptions and a single receipt/detail view.

## Required backend endpoints

The current backend has a subset of this contract. The remaining Lock-first API work should provide:

```text
POST /v1/auth/signup
POST /v1/auth/login
POST /v1/auth/verify-otp
GET  /v1/me
POST /v1/demo/login-as                 # demo only; disabled in production
GET  /v1/vendors
GET  /v1/commitments                   # authenticated member's commitments
POST /v1/commitments/lock
GET  /v1/commitments/preview?code=
POST /v1/commitments/join
POST /v1/consent
GET  /v1/commitments/{commitment_id}
GET  /v1/commitments/{commitment_id}/activity
POST /v1/commitments/{commitment_id}/contribute
POST /v1/commitments/{commitment_id}/cancel
GET  /v1/commitments/{commitment_id}/cycles/{cycle}/voucher
POST /v1/vendors/redeem
GET  /v1/vendors/redemptions
GET  /v1/score/{user_id}
GET  /v1/score/{user_id}/history
GET  /v1/notifications
```

All write operations require authenticated roles and durable idempotency. The actual redemption lifecycle is:

```text
paid cycle → voucher issued → vendor validates → vendor confirms handover → redemption settled
```

