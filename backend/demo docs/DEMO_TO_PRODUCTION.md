# Demo-to-production change register

This document names the gaps in the October 8 regional demo. A feature listed
here must not be described as production-ready in a customer, bank, security,
or regulatory conversation.

## Scope intentionally excluded

- **Sura Float is not shipped.** There is no live credit application,
  underwriting, disbursement, collection, repayment, or lending decision.
- **Sura is non-custodial.** The demo records simulated settlement evidence; it
  does not move money, hold balances, or become lender of record.
- **Sura Score is advisory.** It is an explainable 0–1000 policy score, not a
  credit-bureau score, affordability decision, fraud decision, or automated
  approval/rejection.

## Settlement, Lock, and redemption

| Demo behaviour | Production change | Why it matters |
|---|---|---|
| Contributions, payout completion, voucher issue, and redemption are simulated records. | Integrate bank payment initiation, settlement confirmation, reversal, reconciliation, and ledger references through an institution-specific adapter. | A UI event is not settlement proof. |
| `cancel_and_refund` records `refund_instruction_created`. | Send an idempotent refund instruction to the bank rail, track its status, reconcile the bank reference, and show only a confirmed result. | Sura must not claim a refund moved because an internal record exists. |
| `carry_forward` keeps the unpaid obligation open; no partial voucher is issued. | Product, bank, and legal teams must define the deferred-beneficiary and carried-balance contract before implementing it. | “Proceed short” conflicts with a vendor voucher that cannot be partially redeemed. |
| `cover_shortfall` lets a paid member fill the remaining pool gap after a missed deadline. | Add explicit payer consent, configurable limits, disclosures, bank confirmation, and a reversal model. | Covering another member’s obligation has consumer-protection consequences. |
| Vendor must already be verified to create a Lock. | Allow an unverified merchant selection to create a `vendor_pending` intention; prevent activation, payout, and redemption until verification completes. | This improves discovery without weakening the no-cash vendor lock. |
| Demo vendors and vouchers are seeded. | Build merchant onboarding, review, catalogue management, beneficiary delivery controls, expiry rules, and support tooling. | Seeded records are not an onboarding system. |
| The unresolved-invite replacement route exists but is not in the PWA. | Remove it or design an explicit transfer/substitution protocol with consent, payout-order recalculation, notifications, and audit. | Member substitution is out of scope in the product requirements. |

## API, reliability, and data architecture

| Demo behaviour | Production change | Why it matters |
|---|---|---|
| Only contribution retries have durable idempotency through body `event_id`. | Support an `Idempotency-Key` header on every externally callable write, persist request fingerprints/results, enforce scope and expiry, and publish one error contract. | Clients, bank adapters, and webhook retries need safe replay. |
| API and workers run as one FastAPI service. | Introduce an outbox table, asynchronous workers, dead-letter handling, retry/backoff, alerting, and independently scalable bank-integration workloads. | Database commits and external calls must not leave ambiguous states. |
| Webhook configuration, signatures, test delivery, and logs are present; real Lock/Score events are not dispatched. | Dispatch approved domain events from the outbox; add retry/backoff, retention, key rotation, destination allow-listing, and SSRF protection. | A test webhook is not production event delivery. |
| Contact-resolution rate limiting is application-local. | Use distributed API-gateway limits, tenant quotas, telemetry, abuse detection, and invitation delivery that does not disclose account existence. | Local counters do not protect a public multi-instance deployment. |
| Migrations are tested and deploy through Render. | Add backup/restore drills, migration lock/timeout policy, point-in-time recovery verification, compatibility checks, and zero-downtime standards. | A successful demo migration is not operational resilience. |
| Demo uses one database and synthetic identities. | Separate environments, least-privilege service accounts, data-retention rules, encrypted backups, classification, and audited production access. | Financial data needs strict isolation and governance. |

## Identity, security, and privacy

| Demo behaviour | Production change | Why it matters |
|---|---|---|
| OTP and JWT flows suit a controlled demo. | Use real identity/KYC, hardened MFA, token rotation, device/session policy, account recovery, and penetration testing. | Demo authentication is not regulated onboarding. |
| CORS, rate limits, and deployment settings are demo-focused. | Maintain explicit origin allow-lists, WAF/API-gateway controls, secret rotation, vulnerability management, monitoring, and incident response. | Browser convenience settings must not become exposure. |
| PWA sees first names and vendor-only redemption data. | Conduct privacy, data-minimisation, consent-retention, access-log, DSAR, and data-processing agreement reviews. | Field-level privacy is only one part of compliance. |
| One staff account has full demo permissions. | Add staff lifecycle, least-privilege roles, approval separation, MFA enrollment/recovery, SSO where required, and access reviews. | A permanent all-powerful account is not acceptable in a bank portal. |

## Score, matching, group health, and risk

| Demo behaviour | Production change | Why it matters |
|---|---|---|
| Score weights are deterministic and versioned. The Float/repayment pillar remains unavailable. | Establish policy governance, calibration data, fairness testing, approvals, challenge handling, monitoring, and periodic review. | Explainability does not remove governance obligations. |
| Matching is a deterministic advisory ranker. | Build evaluation datasets, relevance metrics, feedback collection, calibration, drift monitoring, and merchant-quality controls before learned ranking. | It must remain advisory until evidence supports broader use. |
| Group Health is an aggregate advisory signal. | Define bank policy consumers, thresholds, human review, outcome monitoring, and appeal/escalation. | It must not silently block money movement or become hidden credit decisioning. |
| Risk/fraud does not claim verified payment settlement. | Keep fraud ownership separate, integrate the bank’s authoritative transaction data, and document review thresholds. | Sura must not claim to verify a transaction it cannot observe. |

## Contract clean-up before general availability

- The historical TRD reference to daily frequency is superseded by the demo
  contract: **weekly and monthly** are supported. Choose cadence after customer
  research; never silently change it per client.
- The demo fixes grace at **72 hours**. Production may make it a bank/product
  policy, but never an uncontrolled client field.
- The authenticated principal determines the contributor. Production clients
  must never send an arbitrary `user_id` in a contribution request.
- The first-payout cap blocks an oversized genesis Lock rather than silently
  reducing its promised voucher. Production needs approved alternatives and
  clear customer messaging.
- The 0–1000 score scale remains the contract, but no-Float accounts cannot
  earn repayment-pillar points. Product copy must describe available evidence,
  not imply complete credit history.

## Production exit criteria

Do not market the system as production-ready until each applicable row above
has an owner, acceptance test, security review, operational runbook, and
evidence record from a non-demo environment.
