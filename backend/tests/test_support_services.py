from app.services.payout_rules import apply_anchor_and_cap_rule, build_payout_schedule


def test_build_payout_schedule_is_deterministic():
    schedule = build_payout_schedule(["member_a", "member_b", "member_c"], 1500, 3)
    assert schedule == [
        {"cycle": 1, "beneficiary_id": "member_a", "amount": 4500},
        {"cycle": 2, "beneficiary_id": "member_b", "amount": 4500},
        {"cycle": 3, "beneficiary_id": "member_c", "amount": 4500},
    ]


def test_build_payout_schedule_is_empty_without_members():
    assert build_payout_schedule([], 1500, 3) == []


def test_apply_anchor_and_cap_rule_caps_first_cycle_for_genesis_groups():
    capped = apply_anchor_and_cap_rule(25000, 1)
    unchanged = apply_anchor_and_cap_rule(25000, 2)
    assert capped == 10000
    assert unchanged == 25000
