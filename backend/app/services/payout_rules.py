def build_payout_schedule(members: list[str], contribution_amount: int, cycles: int) -> list[dict]:
    if not members:
        return []

    schedule = []
    for cycle in range(1, cycles + 1):
        beneficiary_id = members[(cycle - 1) % len(members)]
        schedule.append({
            "cycle": cycle,
            "beneficiary_id": beneficiary_id,
            "amount": contribution_amount,
        })
    return schedule


def apply_anchor_and_cap_rule(members: list[str], contribution_amount: int, cycle_number: int) -> int:
    if cycle_number != 1:
        return contribution_amount

    cap = 10000
    if len(members) >= 1:
        return min(contribution_amount, cap)

    return contribution_amount
