def _create_paid_cycle(client, auth_headers):
    vendor_id = "vendor_redemption"
    assert client.post(
        "/v1/vendors/verify",
        json={"vendor_id": vendor_id, "name": "Demo Tech Store", "category": "electronics"},
        headers=auth_headers("verifier", role="verifier"),
    ).status_code == 200
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
        headers=auth_headers(vendor_id),
    )
    assert review.status_code == 200

    response = client.post(
        "/v1/vendors/redeem",
        json={"voucher_code": body["voucher_code"]},
        headers=auth_headers(vendor_id),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "settled"

    commitment = client.get(f"/v1/commitments/{commitment_id}", headers=auth_headers("redeemer")).json()
    assert commitment["beneficiaries"][0]["status"] == "redeemed"


def test_redemption_cannot_be_repeated(client, auth_headers):
    commitment_id, _ = _create_paid_cycle(client, auth_headers)
    voucher = client.get(
        f"/v1/commitments/{commitment_id}/cycles/1/voucher", headers=auth_headers("redeemer")
    ).json()
    first = client.post(
        "/v1/vendors/redeem", json={"voucher_code": voucher["voucher_code"]}, headers=auth_headers("vendor_redemption")
    )
    assert first.status_code == 200
    duplicate = client.post(
        "/v1/vendors/redeem", json={"voucher_code": voucher["voucher_code"]}, headers=auth_headers("vendor_redemption")
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
        headers=auth_headers("wrong_vendor"),
    )
    assert response.status_code == 403
