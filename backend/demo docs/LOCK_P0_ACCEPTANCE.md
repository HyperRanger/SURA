# Sura Lock P0 Acceptance Journey

This is the exact backend acceptance story for the demo. It deliberately
proves one shared transaction from three views: member, vendor, and bank.

## Preconditions

- Two verified individual member accounts.
- One verified vendor and one different verified vendor for the rejection step.
- One bank staff session for the same bank as the member accounts.
- Both members have granted score-processing consent.

## Acceptance sequence

1. **Member creates a rotating Lock** with the verified vendor, both selected
   members, a deterministic payout order, and a permitted first payout.
2. **Invited member previews and joins** using the invitation code. The Lock
   becomes active only after all invited members join.
3. **Both members contribute** the exact contribution amount with one stable
   `event_id` each. The last contribution completes the cycle and causes a
   voucher to become ready for that cycle’s beneficiary.
4. **Beneficiary retrieves the voucher.** General commitment reads never
   expose the voucher code.
5. **Wrong vendor validates the voucher** and receives `403`; no settlement is
   recorded.
6. **Correct vendor validates then redeems** the same voucher. The backend
   records one simulated settlement, rejects any replay, and gives the vendor a
   merchant-scoped receipt.
7. **Member refreshes the voucher** and sees `status: redeemed` with a
   redemption timestamp.
8. **Bank inspects the same evidence:** settlement record, settled payout
   schedule, Score update/history, and bank audit-log record.

## Automated proof

`backend/tests/test_member_vendor_bank_journey.py::test_member_vendor_bank_lock_journey`
asserts all eight steps. It is the backend gate for a live walkthrough or
fallback recording.

## Honest demo wording

- Vendor redemption and bank settlement are simulated in this MVP.
- Sura does not verify a real external payment rail.
- The Score is deterministic and explainable; it is not an automated lending
  or fraud decision.
