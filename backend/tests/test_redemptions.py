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
    for user_id in ("redeemer", "contributor"):
        response = client.post(
            f"/v1/commitments/{commitment_id}/contribute", json={"amount": 1500, "event_id": f"evt_{user_id}_cycle_1"},
            headers=auth_headers(user_id),
        )
        assert response.status_code == 200
    return commitment_id, vendor_id


def test_paid_cycle_redeems_to_the_locked_vendor_with_a_voucher(client, auth_headers):
    commitment_id, vendor_id = _create_paid_cycle(client, auth_headers)

    response = client.post(
        f"/v1/commitments/{commitment_id}/redeem", headers=auth_headers("redeemer"),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["vendor_id"] == vendor_id
    assert body["amount"] == 3000
    assert body["status"] == "settled"
    assert body["voucher_code"].startswith("SURA-")

    commitment = client.get(f"/v1/commitments/{commitment_id}", headers=auth_headers("redeemer")).json()
    assert commitment["beneficiaries"][0]["status"] == "redeemed"


def test_redemption_cannot_be_repeated(client, auth_headers):
    commitment_id, _ = _create_paid_cycle(client, auth_headers)
    first = client.post(f"/v1/commitments/{commitment_id}/redeem", headers=auth_headers("redeemer"))
    assert first.status_code == 200
    duplicate = client.post(f"/v1/commitments/{commitment_id}/redeem", headers=auth_headers("redeemer"))
    assert duplicate.status_code == 409


def test_user_cannot_redeem_someone_elses_paid_cycle(client, auth_headers):
    commitment_id, _ = _create_paid_cycle(client, auth_headers)
    response = client.post(f"/v1/commitments/{commitment_id}/redeem", headers=auth_headers("contributor"))
    assert response.status_code == 400
