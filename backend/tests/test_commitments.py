def lock_commitment(client, payload):
    payload = {**payload, "payout_order": payload["members"]}
    vendor_response = client.post(
        "/v1/vendors/verify",
        json={"vendor_id": payload["vendor_id"], "verified": True},
    )
    assert vendor_response.status_code == 200
    return client.post("/v1/commitments/lock", json=payload)


def test_lock_endpoint_creates_commitment(client):
    payload = {
        "type": "rotating",
        "title": "Demo commitment",
        "vendor_id": "vendor_1",
        "contribution_amount": 2000,
        "contribution_frequency": "weekly",
        "cycles": 2,
        "members": ["user_1", "user_2"],
    }

    response = lock_commitment(client, payload)
    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "rotating"
    assert body["status"] == "pending_members"
    assert body["payout_schedule"][0]["cycle"] == 1
    assert body["payout_schedule"][0]["amount"] == 4000


def test_commitment_lifecycle_persists_and_advances_cycle(client):
    lock_payload = {
        "type": "rotating",
        "title": "Lifecycle commitment",
        "vendor_id": "vendor_lifecycle",
        "contribution_amount": 1500,
        "contribution_frequency": "weekly",
        "cycles": 2,
        "members": ["user_lifecycle_a", "user_lifecycle_b"],
    }

    lock_response = lock_commitment(client, lock_payload)
    assert lock_response.status_code == 201
    commitment_id = lock_response.json()["commitment_id"]

    first_contribution = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"user_id": "user_lifecycle_a", "amount": 1500},
    )
    assert first_contribution.status_code == 200
    first_body = first_contribution.json()
    assert first_body["completed_cycle"] is False
    assert first_body["status"] == "active"

    second_contribution = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"user_id": "user_lifecycle_b", "amount": 1500},
    )
    assert second_contribution.status_code == 200
    second_body = second_contribution.json()
    assert second_body["completed_cycle"] is True
    assert second_body["beneficiary"]["user_id"] == "user_lifecycle_a"

    commitment_response = client.get(f"/v1/commitments/{commitment_id}")
    assert commitment_response.status_code == 200
    commitment_body = commitment_response.json()
    assert commitment_body["completed_cycle_count"] == 1
    assert commitment_body["current_cycle_number"] == 2
    assert commitment_body["cycle_states"][0]["status"] == "paid"


def test_contribution_rejects_non_member(client):
    lock_response = lock_commitment(
        client,
        {
            "type": "rotating",
            "title": "Member validation",
            "vendor_id": "vendor_validation",
            "contribution_amount": 900,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["member_a", "member_b"],
        },
    )
    commitment_id = lock_response.json()["commitment_id"]

    response = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"user_id": "outsider", "amount": 900},
    )
    assert response.status_code == 400


def test_contribution_rejects_duplicate_payment_for_cycle(client):
    lock_response = lock_commitment(
        client,
        {
            "type": "rotating",
            "title": "Duplicate protection",
            "vendor_id": "vendor_duplicate",
            "contribution_amount": 1100,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["dup_a", "dup_b"],
        },
    )
    commitment_id = lock_response.json()["commitment_id"]

    first_response = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"user_id": "dup_a", "amount": 1100},
    )
    assert first_response.status_code == 200

    duplicate_response = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"user_id": "dup_a", "amount": 1100},
    )
    assert duplicate_response.status_code == 400


def test_partial_contribution_is_accepted_and_marked_active(client):
    lock_response = lock_commitment(
        client,
        {
            "type": "rotating",
            "title": "Partial contribution",
            "vendor_id": "vendor_partial",
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["partial_a", "partial_b"],
        },
    )
    commitment_id = lock_response.json()["commitment_id"]

    response = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"user_id": "partial_a", "amount": 600},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["contribution_status"] == "partial"
    assert body["cycle_status"] == "active"
    assert body["status"] == "active"


def test_cycle_marks_missed_when_all_members_paid_but_total_is_short(client):
    lock_response = lock_commitment(
        client,
        {
            "type": "rotating",
            "title": "Missed cycle",
            "vendor_id": "vendor_missed",
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["missed_a", "missed_b"],
        },
    )
    commitment_id = lock_response.json()["commitment_id"]

    first = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"user_id": "missed_a", "amount": 1000},
    )
    assert first.status_code == 200

    second = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"user_id": "missed_b", "amount": 600},
    )
    assert second.status_code == 200
    body = second.json()
    assert body["contribution_status"] == "partial"
    assert body["cycle_status"] == "missed"
    assert body["status"] == "missed"
    assert body["beneficiary"]["status"] == "missed"
    assert body["completed_cycle"] is False


def test_completed_commitment_rejects_additional_contributions(client):
    lock_response = lock_commitment(
        client,
        {
            "type": "rotating",
            "title": "Completion guard",
            "vendor_id": "vendor_complete",
            "contribution_amount": 700,
            "contribution_frequency": "weekly",
            "cycles": 1,
            "members": ["complete_a"],
        },
    )
    commitment_id = lock_response.json()["commitment_id"]

    complete_response = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"user_id": "complete_a", "amount": 700},
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["completed_cycle"] is True

    late_response = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"user_id": "complete_a", "amount": 700},
    )
    assert late_response.status_code == 400


def test_genesis_commitment_requires_group_selected_order(client):
    response = client.post(
        "/v1/vendors/verify",
        json={"vendor_id": "vendor_genesis", "verified": True},
    )
    assert response.status_code == 200

    response = client.post(
        "/v1/commitments/lock",
        json={
            "type": "rotating",
            "title": "Genesis order",
            "vendor_id": "vendor_genesis",
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["genesis_a", "genesis_b"],
        },
    )
    assert response.status_code == 400
    assert "payout_order" in response.json()["detail"]


def test_genesis_commitment_rejects_a_pool_above_the_cap(client):
    assert client.post(
        "/v1/vendors/verify",
        json={"vendor_id": "vendor_cap", "verified": True},
    ).status_code == 200

    response = client.post(
        "/v1/commitments/lock",
        json={
            "type": "rotating",
            "title": "Capped genesis pool",
            "vendor_id": "vendor_cap",
            "contribution_amount": 6000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["cap_a", "cap_b"],
            "payout_order": ["cap_a", "cap_b"],
        },
    )
    assert response.status_code == 400
    assert "cap" in response.json()["detail"]


def test_partial_contribution_can_be_recovered(client):
    lock_response = lock_commitment(
        client,
        {
            "type": "rotating",
            "title": "Recover partial payment",
            "vendor_id": "vendor_recovery",
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["recovery_a", "recovery_b"],
        },
    )
    commitment_id = lock_response.json()["commitment_id"]

    assert client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"user_id": "recovery_a", "amount": 600},
    ).status_code == 200
    assert client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"user_id": "recovery_b", "amount": 1000},
    ).json()["status"] == "missed"

    recovered = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"user_id": "recovery_a", "amount": 400},
    )
    assert recovered.status_code == 200
    assert recovered.json()["completed_cycle"] is True
    assert recovered.json()["beneficiary"]["status"] == "paid"
