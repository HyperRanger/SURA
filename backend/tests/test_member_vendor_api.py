"""PWA composition endpoints and real vendor-account identity boundaries."""

from datetime import datetime

from app.main import app
from app.bank.models import BankPartner, BankStaff
from app.models import Commitment, User, Vendor
from core.security import create_token


def _local_headers(user_id: str, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(user_id, {'role': role})}"}


def test_member_home_is_private_and_composes_existing_member_data(client):
    db = app.state.testing_session()
    try:
        db.add(User(id="member_home", name="Member Home", phone="2348000000001", role="individual"))
        db.commit()
    finally:
        db.close()

    response = client.get("/v1/app/home", headers=_local_headers("member_home", "individual"))

    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["user_id"] == "member_home"
    assert body["commitments"] == []
    assert body["active_commitment_count"] == 0
    assert body["next_payout"] is None
    assert 0 <= body["score"]["score"] <= 1000


def test_member_can_resolve_an_exact_contact_and_preview_lock_without_writing(client):
    db = app.state.testing_session()
    try:
        db.add_all(
            [
                User(id="creator", name="Amina Bello", phone="2348000000003", role="individual"),
                User(id="invitee", name="Tunde Okoro", phone="2348000000004", role="individual"),
                Vendor(
                    id="verified_vendor",
                    name="Verified Store",
                    category="electronics",
                    verified_at=datetime.utcnow(),
                ),
            ]
        )
        db.commit()
    finally:
        db.close()

    resolved = client.post(
        "/v1/app/members/resolve",
        json={"phone": "08000000004"},
        headers=_local_headers("creator", "individual"),
    )
    assert resolved.status_code == 200
    assert resolved.json() == {"user_id": "invitee", "first_name": "Tunde"}

    preview = client.post(
        "/v1/app/commitments/lock-preview",
        json={
            "type": "rotating",
            "title": "Laptop group",
            "vendor_id": "verified_vendor",
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["creator", "invitee"],
            "payout_order": ["creator", "invitee"],
        },
        headers=_local_headers("creator", "individual"),
    )
    assert preview.status_code == 200
    assert preview.json()["payout_schedule"][0]["amount"] == 2000
    assert preview.json()["can_create"] is True

    db = app.state.testing_session()
    try:
        assert db.query(Commitment).count() == 0
    finally:
        db.close()


def test_lock_preview_explains_a_blocking_cap_and_rejects_bank_staff(client):
    db = app.state.testing_session()
    try:
        now = datetime.utcnow()
        db.add_all(
            [
                BankPartner(id="lookup_bank", name="Lookup Bank"),
                User(id="cap_creator", name="Cap Creator", phone="2348000000005", role="individual"),
                User(id="staff_member", name="Staff Member", phone="2348000000006", role="individual"),
                Vendor(id="cap_vendor", name="Cap Vendor", category="electronics", verified_at=now),
                BankStaff(
                    id="staff_record",
                    bank_id="lookup_bank",
                    user_id="staff_member",
                    email="staff@lookup.test",
                    password_hash="not-used",
                    role="bank_admin",
                    permissions_json="[]",
                    mfa_phone="2348000000006",
                ),
            ]
        )
        db.commit()
    finally:
        db.close()

    blocked = client.post(
        "/v1/app/commitments/lock-preview",
        json={
            "title": "Too large first payout",
            "vendor_id": "cap_vendor",
            "contribution_amount": 6000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["cap_creator", "staff_member"],
            "payout_order": ["cap_creator", "staff_member"],
        },
        headers=_local_headers("cap_creator", "individual"),
    )
    assert blocked.status_code == 400
    assert "individual Sura accounts" in blocked.json()["detail"]

    db = app.state.testing_session()
    try:
        db.add(User(id="cap_member", name="Cap Member", phone="2348000000007", role="individual"))
        db.commit()
    finally:
        db.close()

    preview = client.post(
        "/v1/app/commitments/lock-preview",
        json={
            "title": "Too large first payout",
            "vendor_id": "cap_vendor",
            "contribution_amount": 6000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["cap_creator", "cap_member"],
            "payout_order": ["cap_creator", "cap_member"],
        },
        headers=_local_headers("cap_creator", "individual"),
    )
    assert preview.status_code == 200
    assert preview.json()["can_create"] is False
    assert preview.json()["blocking_reason"]


def test_vendor_cannot_use_member_lock_or_score_routes(client, auth_headers):
    vendor_headers = auth_headers("not_a_member", role="vendor")
    assert client.get("/v1/commitments", headers=vendor_headers).status_code == 403
    assert client.get("/v1/score/not_a_member", headers=vendor_headers).status_code == 403


def test_contact_resolution_is_durably_rate_limited_per_member(client):
    db = app.state.testing_session()
    try:
        db.add(User(id="lookup_limited", name="Lookup Limited", phone="2348000000008", role="individual"))
        db.commit()
    finally:
        db.close()

    headers = _local_headers("lookup_limited", "individual")
    for _ in range(10):
        response = client.post("/v1/app/members/resolve", json={"phone": "08000000999"}, headers=headers)
        assert response.status_code == 404

    limited = client.post("/v1/app/members/resolve", json={"phone": "08000000999"}, headers=headers)
    assert limited.status_code == 429
    assert int(limited.headers["Retry-After"]) > 0


def test_vendor_session_uses_its_linked_merchant_for_redemption(client, auth_headers):
    from tests.test_redemptions import _create_paid_cycle

    commitment_id, vendor_id = _create_paid_cycle(client, auth_headers)
    voucher = client.get(
        f"/v1/commitments/{commitment_id}/cycles/1/voucher",
        headers=auth_headers("redeemer"),
    ).json()

    db = app.state.testing_session()
    try:
        assert db.get(Vendor, vendor_id) is not None
        db.add(
            User(
                id="vendor_account_user",
                name="Vendor Account",
                phone="2348000000002",
                role="vendor",
                vendor_id=vendor_id,
            )
        )
        db.commit()
    finally:
        db.close()

    review = client.post(
        "/v1/vendors/redeem/validate",
        json={"voucher_code": voucher["voucher_code"]},
        headers=_local_headers("vendor_account_user", "vendor"),
    )
    assert review.status_code == 200

    redeemed = client.post(
        "/v1/vendors/redeem",
        json={"voucher_code": voucher["voucher_code"]},
        headers=_local_headers("vendor_account_user", "vendor"),
    )
    assert redeemed.status_code == 200
    assert redeemed.json()["vendor_id"] == vendor_id

    overview = client.get(
        "/v1/app/vendor/overview",
        headers=_local_headers("vendor_account_user", "vendor"),
    )
    assert overview.status_code == 200
    assert overview.json()["today_redemption_count"] == 1
