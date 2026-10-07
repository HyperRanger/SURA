# Sura Competition Pitch Package

This is the source of truth for the competition deck, spoken pitch, demo handoff,
and judge questions. It reflects the regional demo as it exists today.

## The one-sentence product

Sura gives banks an API for vendor-locked group commitments and an explainable
behavioural score for customers whose income does not arrive as a monthly salary.

## Scope to state clearly

The live regional demo includes Sura Lock and Sura Score.

- **Sura Lock:** a rotating, vendor-locked commitment. Members contribute on a
  schedule; the entitled beneficiary receives a voucher for a verified vendor,
  not cash.
- **Sura Score:** a transparent 0-1000 policy score with an auditable pillar
  breakdown.
- **Simulated settlement:** the demo records settlement evidence. It does not
  move money through a live bank rail.
- **Sura Float:** roadmap only. Do not describe it as built, live, or being
  demonstrated.

Do not claim that Sura is a lender, holds customer funds, verifies a bank
payment it cannot observe, or makes an automated lending decision.

---

## Deck structure

Aim for ten slides and a three-minute spoken pitch. Keep the deck visual. Put
the longer detail in speaker notes, not on the canvas.

## Visual direction and slide master

The deck should feel like an assured financial-product presentation, not a
student project and not a banking dashboard. Use generous space, one decisive
visual idea per slide, and only the evidence needed to support the speaker.

### Format

- **Canvas:** 16:9 widescreen.
- **Safe margins:** 0.65 inches left and right; 0.45 inches top and bottom.
- **Grid:** Twelve columns. Align every title, image edge, caption, and
  diagram to the grid.
- **Background:** Warm off-white `#F8F7F3` on most slides. Use deep indigo
  only for the cover, closing slide, and one deliberate section-break slide.
- **Density:** One headline, one supporting thought, and one visual system per
  slide. A slide should not need an audience member to read paragraphs.

### Sura colour template

Use the colours from the supplied Sura logo. Do not introduce a bright generic
fintech gradient.

| Use | Colour | Hex |
|---|---|---|
| Primary ink and dark backgrounds | Sura indigo | `#29235C` |
| Primary accent | Sura gold | `#D9A441` |
| Main canvas | Warm ivory | `#F8F7F3` |
| Main body text | Ink black | `#16151F` |
| Secondary text and rules | Slate | `#5E6070` |
| Fine dividers | Soft lavender grey | `#DEDDE8` |
| Positive status, sparingly | Forest | `#1E6B52` |
| Attention or warning, sparingly | Burnt orange | `#B84B20` |

Gold should highlight one fact, score point, or active node. It should not
become a second background colour. Do not place gold text on white when it is
small; use indigo or ink for readable body copy.

### Typography

- **Primary font:** Manrope. Use it for all titles, labels, and body copy. If
  Manrope is unavailable, use Aptos or Arial, never multiple substitutes.
- **Slide title:** 34-40 pt, ExtraBold or Bold, indigo on light slides and
  ivory on dark slides.
- **Cover title:** 52-60 pt, ExtraBold.
- **Supporting sentence:** 20-24 pt, Regular, slate or ivory at 80% opacity.
- **Body and labels:** 17-20 pt. Use no text smaller than 15 pt, including
  sources.
- **Numbers:** Bold, large, and quiet. A score can be 70-96 pt; surrounding
  labels remain small.

Avoid all-caps paragraphs, underlining, outline text, and more than two font
weights on a slide.

### Logo use

Use the supplied asset rather than a recreated wordmark:

`frontend/public/sura-logo-horizontal.svg`

- **Cover:** Place the horizontal Sura logo at top left, 0.65 inches from the
  edge. Use the standard indigo wordmark on a light cover or the dark variant
  only when the background demands it.
- **Content slides:** Use the Sura mark only, bottom right, approximately
  0.22 inches high at 35-45% opacity. This is a quiet signature, not a footer
  competing with the slide.
- **Closing slide:** Use the full horizontal logo once, centred or top left.
- **Sim_eco_bank evidence:** Place its name as a small contextual label above
  screenshots. Do not replace Sura branding with the simulated bank identity.
- Never stretch, crop, recolour, shadow, or put the logo inside a rounded
  rectangle.

### Photography, screenshots, and diagrams

- Use real-looking, editorial photographs of Nigerian people only when they
  support the slide's point. Avoid stock-business handshake imagery and people
  staring at floating holograms.
- Use no more than one photo on a slide. Crop it intentionally and leave a
  calm text area.
- Place product screenshots inside a thin indigo device frame with a small
  `LIVE DEMO RECORD` label. Use the actual Sim_eco_bank and Sura screens, not
  invented data.
- Use screenshots on slides 6, 7, and 8. Keep all other slides visual through
  photography, simple editable diagrams, or generous typography.
- Diagrams use thin indigo lines, flat labels, and one gold active path. Avoid
  icons inside every node, gradients, large shadows, and dashed decorative
  connectors.

### Motion and transitions

- Use **Fade** between every slide, duration 0.35-0.45 seconds, with no sound.
- Use **Appear** only to reveal the four stages of Lock on slide 5 and the
  four viewpoints on slide 7. Reveal on click, not automatically.
- Use **Morph** only once: from the Lock journey (slide 5) into the Score
  evidence view (slide 6), if the same cycle marker moves between both slides.
- Do not use bounce, zoom, fly-in, spinning icons, word-by-word animation, or
  animated charts. Motion should clarify sequence, not announce itself.
- Pause on each slide for at least one sentence before advancing. The video
  supplies the product motion; the deck should remain calm.

### Consistency rules

- Use a single left-aligned title position across content slides.
- Keep sources in the lower-left corner at 10-11 pt only where a source is
  actually needed.
- Number only the appendix slides. The main story should not feel like a report.
- Use rounded corners only on live product screenshots. Keep slides, text
  areas, and diagrams flat.
- Remove empty lower-page space by extending the main photograph, diagram, or
  score graphic into that area. Negative space should frame an idea, not look
  unfinished.

### 1. Cover

**Title:** Sura

**Subtitle:** Bank infrastructure for financial commitments and explainable
behavioural data

**On slide:**

- Team name
- Competition name and date
- Sura logo

**Say:**

> A trader, a student, and a freelancer can all manage money responsibly while
> remaining invisible to products designed around monthly salaries. Sura gives
> a bank a way to see structured commitment, then build products around it.

**Layout:** Deep indigo full-bleed background. Place the Sura logo top left.
Set the title in ivory in the lower third. Put a single, high-quality portrait
of a young Nigerian entrepreneur or student on the right, with a very subtle
gold circular detail behind them. Keep the competition name small at bottom
left. Avoid a collage of app screens.

### 2. The customer problem

**Title:** Irregular income leaves useful behaviour invisible

**On slide:**

- A trader earns daily, but not through payroll.
- A student receives money in lumps, then must stretch it.
- A freelancer earns by project, not by month.
- A salary-first underwriting model cannot read their consistency.

**Say:**

> The issue is not that these customers lack financial discipline. The issue is
> that the evidence of that discipline sits outside the signals a conventional
> underwriting process expects.

**Layout:** Ivory background with one wide triptych photo strip: trader,
student, freelancer. Use three short labels below the images. Let the lower
right carry one large indigo line: "Useful behaviour. Little formal evidence."
Do not use unsourced market-size statistics on this slide.

### 3. The bank opportunity

**Title:** A bank can offer the product without rebuilding the infrastructure

**On slide:**

- The bank keeps the customer relationship.
- The bank remains the lender of record when lending applies.
- Transactions stay on the bank's rails.
- Sura provides the commitment logic, score evidence, and API contract.

**Say:**

> Sura does not ask a bank to hand over its customer or become a wallet outside
> the bank. The bank embeds Sura through an API and presents the experience in
> its own channels.

### 4. Sura in one view

**Title:** One API, three connected participants

**On slide:**

```text
Member and vendor experience       Bank console and core systems
                 \                 /
                  \   Sura API    /
                   Lock + Score
                         |
                Bank rails and records
```

**Say:**

> The member creates and fulfils a commitment. The vendor confirms a
> vendor-locked redemption. The bank sees the event trail and an explainable
> score. The same facts travel through one system.

**Layout:** Dark indigo background. Set Member/Vendor on the left and Bank on
the right. Use a large Sura API label in the middle and a thin line dropping to
Bank rails. Gold only marks the active evidence path. Add a small, visible
"Regional demo uses simulated settlement" disclosure at bottom left.

### 5. Sura Lock

**Title:** Sura Lock turns an informal ajo habit into an enforceable contract

**On slide:**

- Members agree contribution amount, schedule, payout order, and vendor.
- Each cycle has a defined beneficiary.
- A paid cycle creates a vendor-specific voucher.
- No cash payout reaches the beneficiary.

**Say:**

> Sura does not decide who deserves the pool. The group decides its terms.
> Sura enforces those terms, records contributions, and prevents the payout
> from becoming unrestricted cash.

**Layout:** Light background with a single horizontal four-stage line:
Agreement, Contributions, Cycle paid, Vendor voucher. Use one gold marker that
moves during the presentation. Anchor the slide with the actual demo goal,
"Laptop Fund rotation". No cards or dashboard tiles.

### 6. Sura Score

**Title:** Sura Score shows the evidence behind the number

**On slide:**

- Score scale: 0-1000
- Commitment behaviour: 35%
- Repayment behaviour: 25% when Float exists
- Transaction stability: 20%
- Institutional verification: 12%
- Social reliability: 8%

**Say:**

> This is a rule-based, versioned policy score. A bank can inspect each pillar
> and the underlying Lock evidence. For the regional build, there is no Float
> repayment evidence, so that pillar does not create an imaginary credit
> history.

**Layout:** Split composition. On the left, place a clean full-height crop of
the live Sim_eco_bank score detail. On the right, show the five pillars as
stacked horizontal rules with their weights. Make the score itself the largest
number on the slide. Never call this an AI credit score.

### 7. The proof, shown from four angles

**Title:** One commitment produces evidence for everyone involved

**On slide:**

- **Member:** creates or joins a laptop rotation and contributes.
- **Second member:** contributes to the same active cycle.
- **Vendor:** validates and redeems the right voucher.
- **Bank:** sees the score, audit trail, Lock evidence, and settlement record.

**Say:**

> We will show this as one connected story, rather than four unrelated product
> demos. It makes the bank API visible: one action creates evidence across the
> member, vendor, and bank views.

**Layout:** Use four evenly sized portrait crops in one band, labelled Member,
Co-member, Vendor, and Bank. Keep labels below the images, not over them. A
gold progress line beneath the band connects the same commitment across all
four views. This is the slide immediately before the separate demo video.

### 8. What the bank integrates

**Title:** A focused API contract for a bank team

**On slide:**

- Customer and score lookup
- Commitment and settlement evidence
- Scoped sandbox API keys
- Signed webhook configuration and test deliveries
- Audit log and tenant-scoped access

**Say:**

> The integration starts with data a bank can inspect safely. It can query a
> customer, open the score explanation, inspect a commitment, and receive
> signed test events. The bank portal demonstrates the controls an integration
> team expects to see.

**Layout:** Use one large Sim_eco_bank screen on the right. On the left, place
four short capability lines, each aligned to a calm indigo rule. Use a small
gold endpoint marker only on the customer-score lookup. Put endpoint details
in an appendix only.

### 9. Commercial model and rollout

**Title:** Sura earns from infrastructure usage

**On slide:**

- API licensing for partner institutions
- Transaction fees on supported commitment activity
- A sandbox-to-pilot path with a partner bank and verified merchants

**Say:**

> The commercial model follows the infrastructure model. Sura earns from API
> access and transaction activity, while the bank keeps its customer
> relationship and financial product ownership.

**Layout:** An understated three-stage timeline across the lower half:
Sandbox, controlled pilot, production integration. Use indigo text and a gold
marker under the current position. Do not invent revenue or traction numbers.

### 10. Close and ask

**Title:** The next proof comes from a controlled bank pilot

**On slide:**

- A sandbox integration partner
- A small verified merchant network
- A controlled cohort of commitment groups
- Bank feedback on score policy and product rules

**Say:**

> We have built the commitment journey and the evidence layer around it. The
> next test is a controlled bank pilot: real policy input, verified merchant
> partners, and a small cohort that can prove whether the behaviour we capture
> improves product access.

**Closing line:**

> Sura helps a bank recognise commitment where its existing data cannot.

**Layout:** Return to the deep indigo background. Use the closing line in large
ivory type, then place the full Sura logo below it. Keep the partner-pilot ask
small and direct in the lower third. End with a clean fade to black.

---

## Three-minute talk track

### 0:00-0:25 — Open with the problem

> A trader can sell every day, a student can receive an allowance once a term,
> and a freelancer can be paid per project. All three may handle money well.
> But without a monthly payslip, a traditional bank product often has no useful
> way to read that behaviour.

### 0:25-0:55 — Explain the bank model

> Sura gives a bank an API that turns structured commitment into evidence. The
> bank keeps its customer relationship and its rails. Sura provides the logic
> for the product and the data trail behind it.

### 0:55-1:30 — Explain Lock

> Our first module is Sura Lock. A group agrees the amount, schedule, payout
> order, and vendor in advance. Everyone contributes. When a cycle completes,
> the rightful beneficiary receives a voucher for the verified vendor, not
> cash. The system enforces what the group already agreed to.

### 1:30-2:00 — Explain Score

> Those events become explainable data in Sura Score. The score runs from zero
> to one thousand. Every point belongs to a visible pillar, including
> commitment behaviour and transaction stability. It is a policy signal a bank
> can audit, not a black-box approval engine.

### 2:00-2:30 — Establish what works now

> In the demo, we show one Lock from the member, vendor, and bank views. The
> bank console queries live seeded records through the deployed API, opens the
> score breakdown, and sees the same commitment's evidence and audit trail.
> Settlement is simulated for this regional build, and Sura Float is roadmap.

### 2:30-3:00 — Close with the ask

> We are asking for a controlled pilot partner: sandbox access, a small set of
> verified merchants, and a cohort of users. That lets a bank test a product
> for customers whose financial discipline exists today, but whose evidence is
> still hard for the system to see.

---

## Demo handoff

Use one sentence before the video:

> Here is one laptop commitment seen by the people who use it and the bank
> that powers it.

Use one sentence after the video:

> That single journey created an enforceable commitment, vendor-specific
> redemption evidence, and an explainable bank-visible score record.

The video should show the member, vendor, and Sim_eco_bank views in that order.
Keep it under ninety seconds. Retain a local copy and an online backup.

---

## Questions judges are likely to ask

### What is real in the demo, and what is simulated?

The deployed backend, database records, Lock rules, Score calculation, vendor
authorization, bank-facing queries, API keys, audit logs, and signed test
webhook flow are real demo software. Settlement is simulated. No live bank
money moves through Sura in this regional build. Sura Float is not shipped.

### Why would a bank use Sura instead of building this itself?

The bank can launch a structured commitment product with a clear data contract,
vendor lock rules, audit evidence, and an explainable score without building
those product rules from the ground up. The bank still owns the customer,
financial rails, and any lending decision.

### Does Sura lend money or hold funds?

No. Sura is designed as an API and decisioning layer. A partner bank remains
the lender of record where lending applies. The regional demo records
simulated settlement rather than moving or holding funds.

### Is Sura Score an AI credit score?

No. It is a deterministic, explainable policy score. The score has named
pillars, documented weights, score history, and an audit trail. A bank can use
it as one input to its policy, not as an automatic approval or rejection.

### What stops a beneficiary from taking cash instead of buying the goal?

The entitlement is tied to a verified vendor. The beneficiary redeems a
vendor-specific voucher; the flow does not create a cash withdrawal route.

### What happens when someone misses a contribution?

The system records the miss and updates the relevant Lock and Score evidence
under the commitment's rules. It does not pretend a missed contribution has
been insured or settled.

### How do you protect the bank's customer data?

The demo applies tenant-scoped bank access, scoped API keys, audited reads,
and server-side storage for the Sim_eco_bank integration key. Production needs
the security and governance work listed in `backend/demo docs/DEMO_TO_PRODUCTION.md`.

### Where does AI fit?

The core financial rules do not depend on an LLM. Matching and group-health
signals are deterministic advisory tools. They can help a bank or a customer
review options, but they do not move money, verify settlement, or make a credit
decision alone.

---

## Presenter checklist

### Before the event

- Confirm the pitch duration and whether judges expect questions during or
  after the deck.
- Export both PPTX and PDF versions of the deck.
- Put the demo video on the presenting computer and a second device.
- Open the deployed API health page before leaving for the venue.
- Keep the current Sim_eco_bank URL and a fallback screen recording available.
- Keep demo credentials and API keys out of the deck, video, and public chat.
- Rehearse until the spoken pitch lands in two minutes and forty seconds. The
  spare twenty seconds belong to pauses, transitions, and interruption.
- Assign one speaker to own the product narrative and one teammate to handle
  architecture and security questions.

### On the day

- Start from the deck, not an IDE or API documentation screen.
- Say "simulated settlement" before a judge has to ask.
- Show the demo only after the audience understands what they are looking at.
- If the live link fails, switch immediately to the recording and continue.
- Do not improvise claims about live bank partnerships, compliance approval,
  real transfers, fraud detection, or Float.

---

## Appendix: feature truth table

| Area | Regional-demo status | How to describe it |
|---|---|---|
| Rotating Sura Lock | Built | A vendor-locked rotating commitment with recorded contributions and payout evidence |
| Vendor redemption | Built for simulated settlement | A verified vendor validates a voucher; no live payout rail is claimed |
| Sura Score | Built | A transparent 0-1000 policy score with visible pillars and audit history |
| Bank portal and integration API | Built for the demo | Tenant-scoped customer, score, Lock, audit, API-key, and signed test-webhook flows |
| Matching | Advisory demo capability | Deterministic recommendations; no automatic enrolment or payout action |
| Group Health | Advisory demo capability | A group-level review signal; it does not block money movement automatically |
| Sura Float | Not built for regional demo | A future module, excluded from the live claim |
| Bank settlement | Simulated | The demo records evidence; a production bank adapter is still required |

## Appendix: sources and evidence

Use product claims from the project documents above. If the deck includes an
external statistic, put the source and publication date in small visible text
on that slide and keep the source link in speaker notes. Do not repeat the
informal-economy percentages in the blueprint unless the presenting team has
checked the original NESG and Moniepoint publications before presenting.
