from app.services.fraud import validate_commitment_rules, validate_vendor_lock


def test_validate_vendor_lock():
    assert validate_vendor_lock("vendor_1", ["vendor_1", "vendor_2"]) is True
    assert validate_vendor_lock("vendor_3", ["vendor_1", "vendor_2"]) is False


def test_validate_commitment_rules():
    assert validate_commitment_rules(2, 1000) is True
    assert validate_commitment_rules(0, 1000) is False
    assert validate_commitment_rules(2, 0) is False

