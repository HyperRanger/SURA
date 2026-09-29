from app.main import app
from app.models import Voucher


def _create_paid_cycle(client, auth_headers):
    vendor_id = "vendor_redemption"
    assert client.post(
        "/v1/vendors/verify",
        json={"vendor_id": vendor_id, "name": "Demo Tech Store", "category": "electronics"},
        headers=auth_headers("verifier", role="verifier"),
    ).status_code == 200
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers("redeemer")).status_code == 200
    lock = client.post(
        "/v1/commitments/lock",
        json={
            "type": "rotating", "title": "Redeem a laptop", "vendor_id": vendor_id,
            "contribution_amount": 1500, "contribution_frequency": "weekly", "cycles": 2,
            "members": ["redeemer", "contributor"], "payout_order": ["redeemer", "contributor"],
        },
        headers=auth_headers("redeemer"),
    )
    assert lock.status_code == 201
    commitment_id = lock.json()["commitment_id"]
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers("contributor")).status_code == 200
    assert client.post(
        "/v1/commitments/join",
        json={"invite_code": lock.json()["invite_code"]},
        headers=auth_headers("contributor"),
    ).status_code == 200
    for user_id in ("redeemer", "contributor"):
        response = client.post(
            f"/v1/commitments/{commitment_id}/contribute", json={"amount": 1500, "event_id": f"evt_{user_id}_cycle_1"},
            headers=auth_headers(user_id),
        )
        assert response.status_code == 200
    return commitment_id, vendor_id


def test_paid_cycle_issues_a_voucher_and_vendor_confirms_redemption(client, auth_headers):
    commitment_id, vendor_id = _create_paid_cycle(client, auth_headers)

    voucher = client.get(
        f"/v1/commitments/{commitment_id}/cycles/1/voucher", headers=auth_headers("redeemer"),
    )
    assert voucher.status_code == 200
    body = voucher.json()
    assert body["vendor_id"] == vendor_id
    assert body["amount"] == 3000
    assert body["status"] == "ready"

    review = client.post(
        "/v1/vendors/redeem/validate",
        json={"voucher_code": body["voucher_code"]},
        headers=auth_headers(vendor_id, role="vendor"),
    )
    assert review.status_code == 200

    response = client.post(
        "/v1/vendors/redeem",
        json={"voucher_code": body["voucher_code"]},
        headers=auth_headers(vendor_id, role="vendor"),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "settled"

    commitment = client.get(f"/v1/commitments/{commitment_id}", headers=auth_headers("redeemer")).json()
    assert commitment["beneficiaries"][0]["status"] == "redeemed"

    activity = client.get(
        f"/v1/commitments/{commitment_id}/activity", headers=auth_headers("redeemer")
    )
    assert activity.status_code == 200
    events = activity.json()
    event_types = [event["event_type"] for event in events]
    assert event_types.index("cycle_paid") < event_types.index("voucher_issued")
    redeemed_event = next(event for event in events if event["event_type"] == "voucher_redeemed")
    assert redeemed_event["actor_user_id"] is None
    assert "voucher_code" not in redeemed_event["details"]


def test_redemption_cannot_be_repeated(client, auth_headers):
    commitment_id, _ = _create_paid_cycle(client, auth_headers)
    voucher = client.get(
        f"/v1/commitments/{commitment_id}/cycles/1/voucher", headers=auth_headers("redeemer")
    ).json()
    first = client.post(
        "/v1/vendors/redeem",
        json={"voucher_code": voucher["voucher_code"]},
        headers=auth_headers("vendor_redemption", role="vendor"),
    )
    assert first.status_code == 200
    duplicate = client.post(
        "/v1/vendors/redeem",
        json={"voucher_code": voucher["voucher_code"]},
        headers=auth_headers("vendor_redemption", role="vendor"),
    )
    assert duplicate.status_code == 409


def test_wrong_vendor_cannot_redeem_a_voucher(client, auth_headers):
    commitment_id, _ = _create_paid_cycle(client, auth_headers)
    voucher = client.get(
        f"/v1/commitments/{commitment_id}/cycles/1/voucher", headers=auth_headers("redeemer")
    ).json()
    response = client.post(
        "/v1/vendors/redeem/validate",
        json={"voucher_code": voucher["voucher_code"]},
        headers=auth_headers("wrong_vendor", role="vendor"),
    )
    assert response.status_code == 403


def test_non_vendor_cannot_access_vendor_redemption_endpoints(client, auth_headers):
    commitment_id, _ = _create_paid_cycle(client, auth_headers)
    voucher = client.get(
        f"/v1/commitments/{commitment_id}/cycles/1/voucher", headers=auth_headers("redeemer")
    ).json()

    validate = client.post(
        "/v1/vendors/redeem/validate",
        json={"voucher_code": voucher["voucher_code"]},
        headers=auth_headers("vendor_redemption"),
    )
    assert validate.status_code == 403

    redeem = client.post(
        "/v1/vendors/redeem",
        json={"voucher_code": voucher["voucher_code"]},
        headers=auth_headers("vendor_redemption"),
    )
    assert redeem.status_code == 403

    history = client.get("/v1/vendors/redemptions", headers=auth_headers("vendor_redemption"))
    assert history.status_code == 403


def test_commitment_endpoints_do_not_expose_voucher_codes(client, auth_headers):
    commitment_id, _ = _create_paid_cycle(client, auth_headers)
    detail = client.get(f"/v1/commitments/{commitment_id}", headers=auth_headers("redeemer"))
    assert detail.status_code == 200
    assert "voucher_code" not in detail.json()["vouchers"][0]


def test_paid_cycle_without_voucher_row_is_lazily_issued_for_beneficiary(client, auth_headers):
    commitment_id, _ = _create_paid_cycle(client, auth_headers)

    db = app.state.testing_session()
    try:
        db.query(Voucher).filter(Voucher.commitment_id == commitment_id, Voucher.cycle_number == 1).delete()
        db.commit()
    finally:
        db.close()

    voucher = client.get(f"/v1/commitments/{commitment_id}/cycles/1/voucher", headers=auth_headers("redeemer"))
    assert voucher.status_code == 200
    body = voucher.json()
    assert body["status"] == "ready"
    assert body["voucher_code"]
