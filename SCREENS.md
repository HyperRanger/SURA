# Sura Screens, Full Inventory and Navigation Map

For the frontend developer. Companion to PRD.md, TRD.md and BUILD_PLAN.md.
The landing page already exists, so it only appears here for the links it must contain.

## How to read this

Every screen has an ID. Use the ID when talking to the team, in branch names and in commit messages, so nobody has to describe a screen in words.

Priority tags:
- **P0** must exist for the October 8 live demo.
- **P1** strengthens the demo, build after every P0 screen works.
- **P2** nice to have, only if time is left. Cut without guilt.

There are four areas, each with its own ID letter.
- **P** public pages, before login
- **M** the member app, for traders, students and freelancers
- **V** the vendor terminal, where vouchers get redeemed
- **B** the bank console, a read only view for the bank partner
- **U** utility and system screens that every area shares

## Rules that apply to every screen

1. Mobile first. Judges will open the demo on their phones. Design for a 390px wide screen and let desktop be the stretched version.
2. Every screen that loads data needs four states built from the start: loading (skeleton), empty, error with a retry button, and normal.
3. Money is always shown in naira with thousands separators, for example ₦17,500. Store and send whole numbers only.
4. Never show one member's Sura Score to another member. The score is private. Members see each other's names and whether they paid, nothing more.
5. Vendors see the beneficiary's first name only, never a phone number or score.
6. A button that sends money or records a contribution must disable itself the moment it is tapped and send an Idempotency-Key. A double tap must never double count.
7. Colours come from the brand palette. Deep Indigo #29235C leads, Sura Gold #D9A441 is used sparingly for success states, locked funds and score highlights, Soft Ivory #F7F5EF is the background, Near Black #171717 is text.

## Sitemap

```
/                          Landing (exists)
/demo                      Demo switcher
/signup  /login  /verify   Auth
/terms  /privacy           Static
/for-banks                 Optional

/app                       Member app (bottom nav: Home, Commitments, Score, Profile)
  /welcome
  /commitments
    /new                   Create wizard (steps 1 to 6, then success)
    /:id                   Detail with tabs: Overview, Schedule, Members, Activity
      /contribute
      /contribute/receipt
      /cycles/:n/voucher
  /join
    /:code                 Preview, then consent, then done
  /consent
  /score
    /history
      /:entryId
    /how-it-works
  /float                   Locked teaser
  /notifications
  /profile
    /verification
    /privacy
    /settings
  /help
  /account-review

/vendor                    Vendor terminal
  /login
  /redeem
    /review
    /success
    /rejected
  /history
    /:id

/bank                      Bank console
  /login
  /commitments
    /:id
  /users
    /:id
  /audit-log
  /flags
    /:id
  /settlements
  /developers
```

## P. Public pages

| ID | Route | Contains | Links to | Pri |
|---|---|---|---|---|
| P1 | / (exists) | Hero, how it works, tagline. Needs working buttons only. | P2 Get started, P3 Log in, P8 Try the demo, P7 For banks, P5 Terms, P6 Privacy in the footer | P0 |
| P2 | /signup | Full name, phone number, "how do you earn" choice (trader, student, freelancer, other), terms checkbox | P4 after submit, P3 if already registered | P0 |
| P3 | /login | Phone number field, continue button | P4 after submit, P2 for new users | P0 |
| P4 | /verify | 6 digit code boxes, resend timer, a small labelled "demo code" hint that only shows in non production | New user goes to M2, returning user goes to M1 | P0 |
| P5 | /terms | Plain static text | Back to wherever the user came from | P2 |
| P6 | /privacy | Plain static text including the data protection notice about score processing | Back | P2 |
| P7 | /for-banks | Short pitch for banks, what the API does, link to the live API docs, contact button | P1, B11 | P2 |
| P8 | /demo | Demo switcher. Buttons to sign in instantly as each seeded person (trader, student, freelancer, and so on), as a vendor, and as the bank. No OTP. Hidden in production. | M1, V2, B2 | P0 |

P8 matters more than it looks. A rotating commitment needs several members to contribute, and the presenter cannot wait for an OTP each time. This page lets you switch people in one tap on stage.

## M. Member app

Bottom navigation on every M screen except the wizard and the voucher: Home, Commitments, Score, Profile.

| ID | Route | Contains | Links to | Pri |
|---|---|---|---|---|
| M1 | /app | Greeting, score chip, active commitments summary, next payout card, two quick actions (Create, Join), any warning banner (missed payment, account review) | M3, M4, M5, M9, M16, M21, M27 | P0 |
| M2 | /app/welcome | Three short cards explaining commitments, vendor lock and the score, then two buttons | M4, M5 | P1 |
| M3 | /app/commitments | Tabs for Active, Pending, Completed. Each row shows title, status badge, progress, next event. Empty state with Create and Join buttons. | M9, M4, M5 | P0 |
| M4 | /app/commitments/new | The create wizard, see the steps below | M9 at the end | P0 |
| M5 | /app/join | Invite code input, join button, error for bad code | M6 | P0 |
| M6 | /app/join/:code | Preview before joining: title, vendor, amount, frequency, cycles, members so far, your payout slot, the payout schedule | M7 if first time, otherwise M8 | P0 |
| M7 | /app/consent | Plain language consent for score processing, what is stored, what is not, agree and decline buttons. Shown once, before the first create or join. | M8 or back to M6 | P0 |
| M8 | /app/join/:code/done | Joined confirmation, who else has joined, what happens next | M9 | P0 |
| M9 | /app/commitments/:id | Detail hub with four tabs, see below | M10, M12, M14 | P0 |
| M10 | /app/commitments/:id/contribute | Cycle number, amount due (prefilled and locked), who has paid so far, confirm button that disables after the tap | M11 | P0 |
| M11 | /app/commitments/:id/contribute/receipt | Success tick, reference number, updated cycle progress. A quiet variant reading "already recorded" when a retry is detected. | M9 | P0 |
| M12 | /app/commitments/:id/cycles/:n/voucher | Only for that cycle's beneficiary. Vendor name, amount, code and QR, expiry, status. States: locked (cycle not complete yet), ready, redeemed, expired. Updates itself when the vendor confirms. | M9 | P0 |
| M13 | (state of M12) | The redeemed state: gold locked funds turn into a completed tick with the vendor and time | M9, M16 | P0 |
| M14 | (modal on M9) | Cancel commitment confirm. Only offered while the commitment is still pending. | M3 | P1 |
| M15 | (sheet on M9 and M1) | Missed contribution notice explaining what it does to the score and eligibility | M16, M19 | P1 |
| M16 | /app/score | Score dial, tier name (for example Unverified), five pillar bars, what unlocks at the next tier, link to history | M17, M19, M20 | P0 |
| M17 | /app/score/history | The audit log. One row per score change with date, reason, points up or down. Filter by pillar. | M18 | P0 |
| M18 | /app/score/history/:entryId | One change in detail: score before and after, which pillar moved, which event caused it, the inputs used | M17, M9 | P1 |
| M19 | /app/score/how-it-works | The five pillars, their weights, and what the score is not (not public, not an academic judgement) | M16 | P1 |
| M20 | /app/float | Locked teaser for Sura Float explaining it unlocks after a first completed commitment. No working form. | M16 | P2 |
| M21 | /app/notifications | List of events: contribution due, cycle complete, voucher ready, flag raised | M9, M12, M27 | P2 |
| M22 | /app/profile | Name, phone, tier, links to the pages below, log out | M23, M24, M25, M26 | P1 |
| M23 | /app/profile/verification | Verification status and what it contributes to the score | M22 | P2 |
| M24 | /app/profile/privacy | What data is used for the score, view and withdraw consent | M22, P6 | P2 |
| M25 | /app/profile/settings | Notification switches, log out | M22 | P2 |
| M26 | /app/help | Short FAQ and how it works | M22 | P2 |
| M27 | /app/account-review | Shown when a fraud flag restricts the account. Explains what is limited, what is still allowed, how to get help. | M1 | P1 |

### M4, the create wizard

One route, six steps, a progress bar at the top, back button on every step. The state must survive a refresh.

| Step | Name | Contains |
|---|---|---|
| M4a | Basics | Title. The three commitment types shown as cards. Rotating is selectable. Collective goal and individual goal are greyed with a "coming soon" label. |
| M4b | Vendor | Pick from the seeded vendor list. Each has name, category and a verified badge. Choice is locked after creation. |
| M4c | Contribution | Amount, frequency (daily or weekly), number of cycles. Live line showing pool per cycle. |
| M4d | Members | Add members by phone number or share the invite code. Shows how many are still needed. |
| M4e | Payout order | If the group is all new, the members choose the order themselves and a notice explains that the first payout is capped. If someone in the group has history, the order is suggested and shown. Drag to reorder where allowed. Includes a small sheet titled "Why is the first payout capped?" |
| M4f | Review | Full summary, the payout schedule, the cap notice if it applies, confirm button |
| M4g | Success | Invite code, copy and share buttons, "waiting for members" status, go to detail |

The reason for M4e is the anchor and cap rule in TRD section 5.1. Backend decides the actual rule. The frontend only displays what the API returns and never works out the order by itself.

### M9, the commitment detail hub

One route with four tabs. A pinned action button at the bottom changes with the situation: Contribute, Show voucher, Share invite code, or nothing.

| Tab | Contains |
|---|---|
| M9a Overview | Status badge, current cycle progress bar, who has paid this cycle, next payout and its beneficiary, the pinned action button |
| M9b Schedule | One row per cycle: cycle number, beneficiary, amount, date, status (scheduled, paid, redeemed). Your own row is highlighted. |
| M9c Members | Name, role, paid or not this cycle, missed count. No scores shown. |
| M9d Activity | Timeline for this commitment: created, member joined, contributed, cycle completed, voucher issued, redeemed |

A pending commitment is the same route showing the waiting state: invite code, share button, member count, cancel option.

## V. Vendor terminal

A separate, very plain area. Big buttons, large text, built for someone standing behind a counter.

| ID | Route | Contains | Links to | Pri |
|---|---|---|---|---|
| V1 | /vendor/login | Vendor code and PIN. The demo switcher can bypass it. | V2 | P0 |
| V2 | /vendor | One large Redeem voucher button, today's total, last few redemptions | V3, V7 | P0 |
| V3 | /vendor/redeem | Code input, optional camera scan | V4, V6 | P0 |
| V4 | /vendor/redeem/review | Amount, beneficiary first name, commitment title, cycle. Confirm handover and reject buttons. | V5, V6 | P0 |
| V5 | /vendor/redeem/success | Receipt, amount, time, note that settlement is simulated | V2 | P0 |
| V6 | /vendor/redeem/rejected | Clear reason: wrong vendor, already redeemed, expired, or invalid code | V3, V2 | P0 |
| V7 | /vendor/history | List of past redemptions | V8, V2 | P1 |
| V8 | /vendor/history/:id | One redemption in detail | V7 | P2 |

V6 is a demo highlight. Trying a voucher at the wrong vendor and watching it get refused is the clearest live proof of vendor lock.

## B. Bank console

Read only. This is what makes the pitch line "it is an API a bank plugs into" visible on screen. Build it after every P0 screen works. B7, B8 and B9 are the ones to build first because they carry the audit log and fraud flag story.

| ID | Route | Contains | Links to | Pri |
|---|---|---|---|---|
| B1 | /bank/login | Simple sign in. The demo switcher can bypass it. | B2 | P1 |
| B2 | /bank | Totals: active commitments, total contributed, completion rate, open fraud flags. Shortcut cards. | B3, B5, B7, B8 | P1 |
| B3 | /bank/commitments | Table of all commitments with type, status, and a badge showing whether it was a new group or a mixed group | B4 | P1 |
| B4 | /bank/commitments/:id | Read only schedule, contributions, the cap decision and why | B3, B6 | P1 |
| B5 | /bank/users | Table of users with score and tier | B6 | P1 |
| B6 | /bank/users/:id | Score, pillar breakdown, that user's audit log, any flags | B5, B7, B9 | P1 |
| B7 | /bank/audit-log | Every score change across all users. Filter by user, pillar and date. Export button. | B6 | P1 |
| B8 | /bank/flags | List of fraud flags with the rule that fired, severity and status | B9 | P1 |
| B9 | /bank/flags/:id | What pattern was detected, the evidence, timeline, and actions: dismiss, confirm, escalate | B8, B6 | P1 |
| B10 | /bank/settlements | Ledger of simulated settlement events | B4 | P2 |
| B11 | /bank/developers | Link to the live API docs at /docs, the endpoint list, a sample request, a placeholder sandbox key | P7 | P2 |

## U. Utility and system screens

The small ones people forget. Build them once, early, and reuse everywhere.

| ID | Screen | Contains | Pri |
|---|---|---|---|
| U1 | Splash | The animated SURA loader while the app boots | P0 |
| U2 | 404 | Page not found with a button home | P0 |
| U3 | Something went wrong | Friendly message, retry button | P0 |
| U4 | No access | Shown when a member opens a commitment they are not part of | P1 |
| U5 | Session expired | Asks the user to log in again and returns them to where they were | P1 |
| U6 | Offline banner | A thin bar when the network drops | P1 |
| U7 | Empty states | Variants for no commitments, no history, no notifications, no flags | P0 |
| U8 | Toasts | Success, error, and the special "already recorded" for a retried contribution | P0 |
| U9 | Confirm modal | Generic yes or no dialog | P0 |
| U10 | Skeletons | Loading placeholders for lists, cards and the score dial | P0 |

## Shared components to build once

Bottom navigation bar, top bar with back button, primary and secondary buttons, text and number inputs, naira amount formatter, status badges (pending, active, completed, missed, flagged), progress bar for cycles, stepper for the wizard, score dial, pillar bar, member chip with initials, bottom sheet, modal, toast, empty state block, skeleton block, QR display, copy to clipboard button, timeline list item.

## Main journeys, by screen ID

Use these as the checklist for the daily full run in BUILD_PLAN.md.

- **A, create a commitment:** P1, P2, P4, M2, M7, M4a to M4g, M9 pending state
- **B, join a commitment:** P8 or P3, P4, M5, M6, M7 (first time only), M8, M9
- **C, contribute:** M1, M9, M10, M11, back to M9
- **D, redeem:** M9, M12 (member), then V2, V3, V4, V5 (vendor), then M13 (member sees it turn redeemed)
- **E, wrong vendor refused:** M12, V3, V6
- **F, check the score and its audit log:** M1, M16, M17, M18
- **G, bank view:** P8, B2, B7, B8, B9

## Endpoints these screens need

Several screens need endpoints that are not in TRD.md yet. Tell Backend now so nobody builds a screen against an endpoint that does not exist. Rows marked new must be added to TRD.md.

| Endpoint | In TRD.md | Used by |
|---|---|---|
| POST /v1/auth/signup, /v1/auth/login, /v1/auth/verify-otp | new | P2, P3, P4 |
| GET /v1/me | new | M1, M22 |
| POST /v1/demo/login-as (demo only, off in production) | new | P8 |
| GET /v1/vendors | new | M4b |
| GET /v1/commitments (mine) | new | M1, M3 |
| POST /v1/commitments/lock | yes | M4 |
| GET /v1/commitments/preview?code= | new | M6 |
| POST /v1/commitments/join | new | M6, M8 |
| POST /v1/consent | new | M7 |
| GET /v1/commitments/{id} | yes | M9 |
| GET /v1/commitments/{id}/activity | new | M9d |
| POST /v1/commitments/{id}/contribute (with Idempotency-Key) | yes | M10, M11 |
| POST /v1/commitments/{id}/cancel | new | M14 |
| GET /v1/commitments/{id}/cycles/{n}/voucher | new | M12 |
| POST /v1/vendors/verify | yes | seeding |
| POST /v1/vendors/redeem | new | V3, V4, V5, V6 |
| GET /v1/vendors/redemptions | new | V2, V7, V8 |
| GET /v1/score/{user_id} | yes | M16 |
| GET /v1/score/{user_id}/history | new | M17, M18, B6 |
| GET /v1/notifications | new | M21 |
| GET /v1/flags, GET /v1/flags/{id}, POST /v1/flags/{id}/resolve | new | B8, B9, M27 |
| GET /v1/bank/overview, /v1/bank/users, /v1/bank/audit-log | new | B2, B5, B7 |

## Suggested build order for the frontend

1. Shell first: routing for every route above, bottom nav, top bar, U1 to U10, brand colours, naira formatter. Everything else plugs into this.
2. P2, P3, P4 and P8 so people can get in, and so the team can switch accounts.
3. M4 (the wizard), M5, M6, M7, M8. This unblocks everyone else's testing.
4. M9, M10, M11.
5. M12, M13 and V1 to V6. This finishes the money flow from contribution to redemption.
6. M16, M17, M1, M3.
7. Everything tagged P1, starting with the bank console B7, B8, B9.
8. P2 items last, and drop any of them without discussion if time is short.

## Counts

64 screens in the main tables: 32 are P0, 20 are P1 and 12 are P2.

By area: public 8, member app 27, vendor terminal 8, bank console 11, utility 10.

On top of that, the create wizard has 7 steps (M4a to M4g) and the commitment detail hub has 4 tabs (M9a to M9d). These are not counted separately above because they live on one route each.

If the team is short on time, the P0 list alone is a complete, demoable product. Everything else makes it stronger but none of it is required.
