# Sura Build Plan, Team Task Tracker

Companion to PRD.md and TRD.md. This document exists for one reason: so no two people ever end up building the same thing, and nobody sits idle wondering what to do next.

## How to use this

- Each task has exactly one owner. If a task feels like it needs two people, split it into two smaller tasks with one owner each. Do not share ownership of one line item.
- Each task lists what it is waiting on. Do not start a task until everything it is waiting on is checked off.
- If you finish your current task and the next one is still blocked, say so in the daily sync instead of starting something out of order.
- Daily sync: 15 minutes, same time every day starting September 24. Each person says what they finished, what they are doing next, and what is blocking them. This is where duplicate work gets caught before it happens, not after.

---

## Phase 0 — September 22 to 23: Setup

Nothing here waits on anything else. All four of you can work in parallel today.

- [ ] Backend Core: Postgres running locally, schema migrated from TRD section 3
- [ ] Backend Core: confirm all four teammates have repo access and can clone it
- [ ] Backend AI/ML: score formula from TRD section 5.2 written as a standalone function, tested by hand against fake numbers, not wired to any API yet
- [ ] Frontend: React project scaffolded, routing stubbed for the four screens in PRD section 7, no API calls yet
- [ ] UI/UX: wireframes for create, contribute, redeem, and score screens

---

## Phase 1 — September 24 to 28: Core Build

- [ ] Backend Core: POST /v1/commitments/lock implemented for real
  - Waiting on: schema migrated (Phase 0)
- [ ] Backend Core: the anchor and cap rule (TRD 5.1) implemented inside the lock endpoint
  - Waiting on: lock endpoint skeleton existing
- [ ] Backend Core: POST /v1/commitments/{id}/contribute implemented
  - Waiting on: lock endpoint done
- [ ] Backend Core: deploy to Railway or Render, not local only
  - Waiting on: lock and contribute endpoints working locally
- [ ] Backend AI/ML: GET /v1/score/{user_id} wired to real database events
  - Waiting on: contribute endpoint emitting real events
- [ ] Frontend: create commitment screen wired to the deployed API
  - Waiting on: lock endpoint deployed, not just local
- [ ] Frontend: join commitment screen, invite code flow
  - Waiting on: lock endpoint returning invite codes
- [ ] UI/UX: visual design system finalized and shared with Frontend as a short style reference
  - Waiting on: nothing; do this as early in the week as possible
- [ ] UI/UX: slide deck skeleton, section headers only, no content yet
  - Waiting on: nothing

Important: Backend Core should deploy to a real shared environment by day two of this phase, not stay on localhost. If Frontend builds against someone's laptop, everyone drifts out of sync without noticing. Building against one shared deployed URL is what actually prevents duplicate, conflicting versions of the same feature.

---

## Phase 2 — September 29 to October 3: Full Cycle Working

- [ ] Backend Core: vendor verify endpoint, 2 to 3 real vendors seeded
  - Waiting on: nothing new; can start anytime
- [ ] Backend Core: redemption logic, mark a cycle paid, generate a voucher or code
  - Waiting on: contribute endpoint correctly detecting a completed cycle
- [ ] Backend AI/ML: confirm the score updates correctly across a full multi cycle rotation, not just the first cycle
  - Waiting on: at least two full test commitments existing in the database
- [ ] Frontend: contribute screen wired to the real endpoint
  - Waiting on: contribute endpoint deployed
- [ ] Frontend: redemption or voucher screen
  - Waiting on: redemption logic deployed
- [ ] Frontend: score dashboard wired to the real score endpoint
  - Waiting on: score endpoint deployed
- [ ] UI/UX: write the actual demo script against the real, working product
  - Waiting on: one full cycle working end to end, at least once

---

## Phase 3 — October 4 to 6: Integration and Polish

- [ ] Whole team together, same call or room: run the full flow, create through redeem through score, once a day, everyone watching, not just the person who built that piece
- [ ] Backend Core: seed clean, realistic demo data for the actual pitch
- [ ] UI/UX: finalize deck content using real screenshots from the working product
- [ ] Backend Core and Frontend: fix whatever breaks during the daily full run on the same day; do not let bugs queue up into the final week

---

## Phase 4 — October 7 to 8: Rehearsal and Pitch

- [ ] Two full timed rehearsals on October 7, whole team present
- [ ] A screen recorded backup of one clean, successful full run, saved somewhere everyone can reach on the morning of October 8
- [ ] October 8: the pitch

---

## Rules that prevent duplicate work

- One person owns the schema. That is Backend Core. Everyone else reads models.py; nobody else edits it without telling Backend Core first.
- Frontend never guesses at what an API returns. If a response shape is not already written down in TRD.md, ask Backend Core before writing code that assumes it.
- No task on this list has two owners. If something feels too big for one person, split it into two separate checklist items instead of assigning both names to one item.
- The daily sync is not optional. Most duplicate work happens because two people quietly built the same thing on the same day without saying so out loud first.

---

## Summary

This plan is designed to keep the team aligned, reduce duplicate work, and make sure every task has a clear owner and blocker list. The key principle is simple: do not start until the dependency is actually ready.
