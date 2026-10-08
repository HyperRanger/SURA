"""One production-shaped proof for the Member -> Vendor -> Bank story."""

from datetime import datetime

from app.bank.models import BankPartner, BankStaff
from app.main import app
from app.models import User, Vendor
from core.security import create_token


def _headers(user_id: str, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(user_id, {'role': role})}"}


def test_member_vendor_bank_lock_journey(client):
    """A bank can explain the same completed Lock seen by its users and vendor."""
    db = app.state.testing_session()
    try:
        now = datetime.utcnow()
        db.add_all(
            [
                BankPartner(id="bank_journey", name="Journey Bank"),
                User(
                    id="journey_amara",
                    name="Amara Okafor",
                    phone="2348000000011",
                    role="individual",
                    bank_id="bank_journey",
                    bank_customer_id="JRN-001",
                    verified_at=now,
                ),
                User(
                    id="journey_tunde",
                    name="Tunde Adeyemi",
                    phone="2348000000012",
                    role="individual",
                    bank_id="bank_journey",
                    bank_customer_id="JRN-002",
                    verified_at=now,
                ),
                Vendor(
                    id="journey_vendor",
                    name="Campus Electronics",
                    category="electronics",
                    verified_at=now,
                ),
                Vendor(
                    id="journey_wrong_vendor",
                    name="Wrong Store",
                    category="electronics",
                    verified_at=now,
                ),
                User(
                    id="journey_vendor_user",
                    name="Campus Electronics Operator",
                    phone="2348000000013",
                    role="vendor",
                    vendor_id="journey_vendor",
                ),
                User(
                    id="journey_wrong_vendor_user",
                    name="Wrong Store Operator",
                    phone="2348000000015",
                    role="vendor",
                    vendor_id="journey_wrong_vendor",
                ),
                User(id="journey_bank_staff_user", name="Bank Staff", phone="2348000000014", role="individual"),
                BankStaff(
                    id="journey_bank_staff",
                    bank_id="bank_journey",
                    user_id="journey_bank_staff_user",
                    email="journey.staff@bank.test",
                    password_hash="not-used-in-this-session-test",
                    role="bank_admin",
                    permissions_json="[]",
                    mfa_phone="2348000000014",
                ),
            ]
        )
        db.commit()
    finally:
        db.close()

    amara_headers = _headers("journey_amara", "individual")
    tunde_headers = _headers("journey_tunde", "individual")
    vendor_headers = _headers("journey_vendor_user", "vendor")
    wrong_vendor_headers = _headers("journey_wrong_vendor_user", "vendor")
    bank_headers = _headers("journey_bank_staff_user", "bank_admin")

    assert client.post("/v1/consent", json={"granted": True}, headers=amara_headers).status_code == 200
    assert client.post("/v1/consent", json={"granted": True}, headers=tunde_headers).status_code == 200

    created = client.post(
        "/v1/commitments/lock",
        json={
            "type": "rotating",
            "title": "Amara's laptop",
            "vendor_id": "journey_vendor",
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["journey_amara", "journey_tunde"],
            "payout_order": ["journey_amara", "journey_tunde"],
        },
        headers=amara_headers,
    )
    assert created.status_code == 201
    commitment_id = created.json()["commitment_id"]

    assert client.post(
        "/v1/commitments/join",
        json={"invite_code": created.json()["invite_code"]},
        headers=tunde_headers,
    ).status_code == 200
    assert client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1000, "event_id": "journey-amara-cycle-1"},
        headers=amara_headers,
    ).status_code == 200
    paid = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1000, "event_id": "journey-tunde-cycle-1"},
        headers=tunde_headers,
    )
    assert paid.status_code == 200
    assert paid.json()["completed_cycle"] is True

    voucher = client.get(
        f"/v1/commitments/{commitment_id}/cycles/1/voucher", headers=amara_headers
    )
    assert voucher.status_code == 200
    assert voucher.json()["status"] == "ready"

    wrong_vendor = client.post(
        "/v1/vendors/redeem/validate",
        json={"voucher_code": voucher.json()["voucher_code"]},
        headers=wrong_vendor_headers,
    )
    assert wrong_vendor.status_code == 403

    review = client.post(
        "/v1/vendors/redeem/validate",
        json={"voucher_code": voucher.json()["voucher_code"]},
        headers=vendor_headers,
    )
    assert review.status_code == 200
    assert review.json()["beneficiary_first_name"] == "Amara"
    redeemed = client.post(
        "/v1/vendors/redeem",
        json={"voucher_code": voucher.json()["voucher_code"]},
        headers=vendor_headers,
    )
    assert redeemed.status_code == 200
    assert redeemed.json()["commitment_title"] == "Amara's laptop"
    assert redeemed.json()["beneficiary_first_name"] == "Amara"

    member_voucher = client.get(
        f"/v1/commitments/{commitment_id}/cycles/1/voucher", headers=amara_headers
    )
    assert member_voucher.status_code == 200
    assert member_voucher.json()["status"] == "redeemed"
    assert member_voucher.json()["redeemed_at"] is not None

    settlement = client.get("/v1/bank/settlements", headers=bank_headers)
    assert settlement.status_code == 200
    assert settlement.json()[0]["commitment_id"] == commitment_id

    score = client.get("/v1/bank/users/journey_amara/score", headers=bank_headers)
    assert score.status_code == 200
    assert 0 <= score.json()["current"]["score"] <= 1000
    assert score.json()["history"]

    audit = client.get("/v1/bank/audit-log?user_id=journey_amara", headers=bank_headers)
    assert audit.status_code == 200
    assert any(event["type"] == "score" for event in audit.json())

    evidence = client.get(f"/v1/bank/commitments/{commitment_id}", headers=bank_headers)
    assert evidence.status_code == 200
    assert evidence.json()["payout_schedule"][0]["settlement_status"] == "settled"
