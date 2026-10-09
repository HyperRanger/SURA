"""Explicit partner visibility and masked vendor payout labels."""

from datetime import datetime

from app.bank.models import BankPartner
from app.main import app
from app.models import LinkedAccount, User, Vendor, VendorPayoutAccount
from core.security import create_token


def _headers(user_id: str, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(user_id, {'role': role})}"}


def _setup(client) -> None:
    db = app.state.testing_session()
    try:
        db.add_all([
            BankPartner(id="bnk_partner_test", name="Beacon Bank", environment="sandbox"),
            User(id="member_partner_test", name="Amina Bello", phone="2348003300001", role="individual"),
            Vendor(id="vendor_payout_test", name="Lagos Tools", category="hardware", verified_at=datetime.utcnow()),
            User(id="vendor_payout_user", name="Tolu Tools", phone="2348003300002", role="vendor", vendor_id="vendor_payout_test"),
        ])
        db.commit()
    finally:
        db.close()


def test_member_must_explicitly_consent_before_a_partner_can_see_them(client):
    _setup(client)
    headers = _headers("member_partner_test", "individual")

    listed = client.get("/v1/banks", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["sura_supported_banks"] == [{
        "bank_id": "bnk_partner_test", "name": "Beacon Bank", "environment": "sandbox",
    }]

    no_consent = client.post("/v1/accounts/link", json={
        "bank_name": "Beacon Bank", "account_number": "0123456789", "partner_bank_id": "bnk_partner_test",
    }, headers=headers)
    assert no_consent.status_code == 201, no_consent.text

    db = app.state.testing_session()
    try:
        assert db.get(User, "member_partner_test").bank_id is None
        assert db.query(LinkedAccount).one().partner_bank_id is None
    finally:
        db.close()

    consented = client.post("/v1/accounts/link", json={
        "bank_name": "Beacon Bank", "account_number": "0123456789", "partner_bank_id": "bnk_partner_test", "share_with_partner": True,
    }, headers=headers)
    assert consented.status_code == 201, consented.text
    assert consented.json()["sura_partner"]["bank_id"] == "bnk_partner_test"

    db = app.state.testing_session()
    try:
        member = db.get(User, "member_partner_test")
        assert member.bank_id == "bnk_partner_test"
        assert member.bank_customer_id
        row = db.query(LinkedAccount).one()
        assert row.account_number_masked == "ending 6789"
        assert "0123456789" not in str(row.__dict__)
    finally:
        db.close()


def test_vendor_can_save_only_a_masked_payout_label(client):
    _setup(client)
    headers = _headers("vendor_payout_user", "vendor")

    resolved = client.post("/v1/vendors/me/payout-account/resolve", json={
        "bank_name": "GTBank", "account_number": "1234567890",
    }, headers=headers)
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["account_number_masked"] == "ending 7890"

    saved = client.put("/v1/vendors/me/payout-account", json={
        "bank_name": "GTBank", "account_number": "1234567890",
    }, headers=headers)
    assert saved.status_code == 200, saved.text
    assert saved.json()["simulated"] is True

    current = client.get("/v1/vendors/me/payout-account", headers=headers)
    assert current.status_code == 200
    assert current.json()["account"]["account_number_masked"] == "ending 7890"

    db = app.state.testing_session()
    try:
        row = db.query(VendorPayoutAccount).one()
        assert row.vendor_id == "vendor_payout_test"
        assert "1234567890" not in str(row.__dict__)
    finally:
        db.close()
