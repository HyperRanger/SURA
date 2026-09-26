GENESIS_FIRST_PAYOUT_CAP = 10_000


def build_payout_schedule(members: list[str], contribution_amount: int, cycles: int) -> list[dict]:
    if not members:
        return []

    pooled_cycle_amount = contribution_amount * len(members)
    schedule = []
    for cycle in range(1, cycles + 1):
        beneficiary_id = members[(cycle - 1) % len(members)]
        schedule.append({
            "cycle": cycle,
            "beneficiary_id": beneficiary_id,
            "amount": pooled_cycle_amount,
        })
    return schedule


def apply_anchor_and_cap_rule(payout_amount: int, cycle_number: int) -> int:
    if cycle_number != 1:
        return payout_amount

    return min(payout_amount, GENESIS_FIRST_PAYOUT_CAP)
