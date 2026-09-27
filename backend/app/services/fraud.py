from collections.abc import Iterable


def validate_vendor_lock(vendor_id: str, allowed_vendor_ids: Iterable[str]) -> bool:
    return vendor_id in allowed_vendor_ids


def validate_commitment_rules(member_count: int, commitment_amount: int | float) -> bool:
    return member_count > 0 and commitment_amount > 0
