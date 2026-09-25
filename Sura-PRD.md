# Sura Product Requirements Document

Version 1.0  
Prepared for InnovateX 2026, Inclusive Finance track  
Regional pitch date: October 8, 2026  
Status: active build

---

## 1. Overview

Sura is API infrastructure that lets a bank or fintech offer structured financial commitments to people whose income does not arrive as a monthly salary. It has three parts that share one engine.

- Sura Lock is a programmable commitment product. A group of people contribute money on a schedule, and the platform enforces who is entitled to the pooled funds, when, and what they can spend it on.
- Sura Score is a transparent, rule-based reputation engine. It turns completed commitments into a score a bank can use for underwriting, without needing a credit bureau history.
- Sura Float is a small, self-enforcing fee advance product. It is explicitly out of scope for the October 8 regional build. See section 5.

---

## 2. Problem Statement

A trader who turns over cash daily, a student whose allowance lands once a term, and a freelancer paid in bursts between gigs all share one problem. None of them has a payslip, so none of them is visible to a bank's underwriting model. They are not unreliable; they are just invisible to a system built around salaries.

Roughly 93 percent of employed Nigerians work outside the formal payroll system (NESG, 2025), and more than half of that informal workforce is under 34 (Moniepoint, 2025). This is not a small edge case. It is the default financial life for most young Nigerians.

---

## 3. Target Users

### Trader
Runs a small business with daily cash income. Already understands rotating group savings (ajo) informally. Wants a safer version that cannot be run off with.

### Student
Allowance or fees land in lump sums. Needs to save toward a specific goal with peers, or cover a small recurring fee on time.

### Freelancer
Gig or project-based income (a musician, a developer, any contract worker). Wants to build toward equipment or a goal despite irregular income.

### Bank or fintech (the actual buyer)
Wants a new product it can launch fast, without building underwriting infrastructure from scratch, and without taking on data or lending risk it has not planned for.

---

## 4. Product Principles

These are the rules the product must never break, because they are also the answers to the hardest questions judges and partners will ask.

- Sura never decides who benefits from a commitment. It only enforces the terms a group already agreed to.
- Every payout is vendor locked. Funds never become cash in a user's hand.
- A new user with zero history is never treated the same as one with a track record, and the product says exactly what a new user can and cannot do.
- Every cost of credit is disclosed as a number, in naira and as an annualized rate, before it is charged. Nothing is framed to feel smaller than it is.
- Sura never holds funds. It instructs a bank's own rails to move money.

---

## 5. Regional MVP Scope (October 8)

We have from today (September 22) to the regional pitch on October 8, about 17 days, with a team of four. The scope below is deliberately narrow. Everything else in this document and in the full product blueprint is roadmap, not a claim about what will exist on October 8.

### 5.1 In scope for the live demo

- One commitment type only: Rotating. Collective goal and individual goal types are designed and documented, but not built for this demo.
- The full rotating commitment lifecycle: create, invite members, contribute, reach a payout cycle, redeem at a vendor.
- The anchor and cap rule for a brand new group (see TRD section 5.1). This is what makes the live demo work at all, since a demo group is by definition all new.
- Sura Score, showing a real score and its pillar breakdown, computed from actual demo data, not hardcoded.
- Vendor lock against 2 to 3 real, named merchants.
- A simulated bank settlement layer standing in for a real Blaze or POS integration. This is stated out loud in the pitch, not hidden.

### 5.2 Explicitly out of scope for October 8

- Sura Float, in full. It is documented in the blueprint and mentioned in the pitch as the second module the same engine already supports, but no working Float code ships for the regional demo. Revisit if the team advances to the October 30 grand finale.
- Collective goal and individual goal commitment types.
- Multi-institution fee calendars.
- Any real, production bank integration. The demo runs against simulated settlement throughout.
- Vendor onboarding tooling. The 2 to 3 demo vendors are set up by hand, not through a built flow.

### 5.3 Why this cut, specifically

Two working modules, half built, lose to one module that works perfectly, every time, in front of a judge. Sura Lock is also the module that carries the strongest, most defensible story (the rotating commitment fix, the anchor and cap rule, the vendor lock mechanic). Float depends on a repayment and disclosure story that is real but needs more build time than 17 days allows to get right without cutting corners on the honesty commitments in section 4.

---

## 6. Feature Requirements

Priority key:
- P0 = must work for the demo to succeed
- P1 = strengthens it if time allows
- P2 = roadmap only

### 6.1 Sura Lock, rotating commitments (P0)

- A user can create a rotating commitment with a title, a contribution amount, a frequency (daily or weekly), a number of cycles, and a list of invited members.
- Each invited member can join via an invite code.
- Each member can record a contribution against the current cycle.
- When a cycle's total is reached, the system generates a payout entitlement for that cycle's beneficiary.
- The beneficiary order follows the anchor and cap rule (TRD 5.1), not a naive first-to-join order.
- A payout is redeemed only against a vendor already verified on the simulated bank network, never as a cash withdrawal.

### 6.2 Sura Score (P0)

- Every verified user has a score, starting from a defined baseline (see TRD 5.2).
- The score updates after every contribution, completed cycle, and missed contribution.
- The score is shown with its full pillar breakdown, not just a single number, since the transparency of the breakdown is a core part of the pitch.

### 6.3 Vendor lock and redemption (P0)

- A small, fixed list of 2 to 3 real vendors is seeded in the database.
- A commitment can only be linked to a vendor from this list.
- Redemption generates a voucher or code tied to the commitment and the specific cycle's beneficiary, not to any other member.

### 6.4 Missed contribution handling (P1)

- If a member misses a scheduled contribution, the system flags it and updates that member's score.
- No stake pool, no insurance product. This was deliberately removed from the design (see blueprint, Product Modules).

### 6.5 Sura Float (P2, roadmap only)

Documented for the pitch. Not built for October 8.

---

## 7. User Flows

### Flow A: Create and join a rotating commitment

- User A creates a commitment (title, amount, frequency, cycles, vendor).
- User A invites members B, C, D, E via an invite code.
- Each member joins, and the commitment becomes active once all members have joined.

### Flow B: Contribute and reach a payout

- Each member contributes on the agreed schedule.
- Once cycle 1's total is reached, the system computes cycle 1's beneficiary per the anchor and cap rule.
- That beneficiary receives a redemption voucher for the linked vendor.

### Flow C: Redeem at a vendor

- The beneficiary presents the voucher (a code or QR shown on screen) at the vendor.
- The system marks that cycle as redeemed.
- The commitment moves to the next cycle.

### Flow D: View score

- A user opens their score dashboard.
- The dashboard shows the current score and its pillar breakdown, computed from that user's real commitment history.

---

## 8. Success Metrics

For the regional pitch specifically, success is binary and demo-focused, not growth-focused:

- The full Flow A through Flow D runs live, on stage, without a hardcoded value standing in for real data.
- The judges can ask, "show me the code paying out" and see it happen in front of them.
- The score shown on stage is computed from actions taken earlier in the same demo, not seeded in advance.

Longer-term product metrics (completion rate, default rate, time to first commitment) belong in the full blueprint and are not regional demo requirements.

---

## 9. Non-Functional Requirements

- The demo must run on a public URL reachable from a judge's own phone, not only on a laptop on stage.
- Basic error handling only. The demo path must not crash, but edge cases outside the demo script do not need full coverage by October 8.
- No real personal data. All demo users, vendors, and institutions are clearly fictional or clearly marked as illustrative.

---

## 10. Assumptions and Open Questions

- Assumes the regional pitch format allows a live, browser-based demo (to be confirmed with organizers).
- Assumes all four team members have working local environments by September 24 (see TRD section 7).
- Open question: does the regional round require a slide deck, a live demo, or both? Confirm with organizers this week, since it changes how much UI polish is worth investing versus API polish.

---

## 11. Timeline

See TRD section 10 for the full day-by-day task breakdown by role. At a glance:

- September 22 to 23: scope lock, environment setup, schema finalized.
- September 24 to 28: core backend and frontend built in parallel against the real schema.
- September 29 to October 3: full rotating cycle working end to end, score live.
- October 4 to 6: integration testing, demo data seeded, deck and script finalized.
- October 7 to 8: rehearsal, then the regional pitch.
