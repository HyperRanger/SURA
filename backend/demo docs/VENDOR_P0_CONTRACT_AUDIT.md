# Vendor P0 Backend Contract Audit

Audit date: 2026-09-30  
Scope: Vendor terminal screens V1–V8 and the member-to-vendor redemption handoff.

## Result: complete

| Screen / capability | Contract | Status | Enforced backend rule |
|---|---|---|---|
| V1 vendor session | Auth flow and `GET /v1/me` | Ready | The server assigns the vendor role and linked merchant record; a client route or submitted vendor ID grants nothing. |
| V2 dashboard | `GET /v1/app/vendor/overview` | Ready | Returns the session-derived merchant profile/verification state, today’s simulated settlement totals, and recent records. |
| V3 voucher input | `POST /v1/vendors/redeem/validate` | Ready | The request contains only `voucher_code`; merchant identity comes from the signed-in vendor account. |
| V4 handover review | validation response | Ready | Includes voucher state, amount, cycle, commitment title, and beneficiary first name only. |
| V4 confirm | `POST /v1/vendors/redeem` | Ready | Creates one simulated settlement atomically, marks voucher/beneficiary redeemed, and returns a receipt payload. |
| V5 success receipt | redemption response | Ready | Returns receipt ID, commitment title, beneficiary first name, amount, status, and timestamp. |
| V6 rejected state | validation/redeem errors | Ready | Wrong vendor `403`; invalid code `404`; already redeemed `409`; unavailable/not-ready `400`. |
| V7 history | `GET /v1/vendors/redemptions` | Ready | Returns only the authenticated merchant’s records with safe receipt display fields. |
| V8 receipt detail | `GET /v1/vendors/redemptions/{redemption_id}` | Ready | Merchant-scoped; another merchant receives `404`, so record existence is not disclosed. |

## Non-negotiable privacy and authority rules

- The PWA must never send `vendor_id` during voucher validation, redemption,
  history, or receipt lookup.
- A vendor sees a beneficiary’s first name, not phone number, Score, or full
  profile.
- Voucher codes never appear in general commitment reads or activity events.
  They appear only in beneficiary voucher reads and authenticated vendor flows.
- Validation is not settlement. The terminal must validate, ask for handover
  confirmation, then call redeem.
- Settlement is simulated in this MVP; the UI must state that plainly.

## Verified acceptance path

`member voucher ready → wrong vendor rejected → correct vendor validates →
correct vendor redeems once → vendor receipt/history → member sees redeemed
state → bank sees settlement evidence`

This path is covered by the member/vendor/bank journey and redemption tests.
