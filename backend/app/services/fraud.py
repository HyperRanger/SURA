def validate_vendor_lock(vendor_id: str, allowed_vendors: list[str]) -> bool:
    return vendor_id in allowed_vendors


def validate_commitment_rules(member_count: int, contribution_amount: int) -> bool:
    return member_count > 0 and contribution_amount > 0
