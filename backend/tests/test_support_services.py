from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def lock_commitment(client, auth_headers, payload):
    payload = {**payload, "payout_order": payload["members"]}
    vendor_response = client.post(
        "/v1/vendors/verify",
        json={"vendor_id": payload["vendor_id"], "verified": True},
        headers=auth_headers("verifier_user", role="verifier"),
    )
    assert vendor_response.status_code == 200
    assert client.post(
        "/v1/consent", json={"granted": True}, headers=auth_headers(payload["members"][0])
    ).status_code == 200
    return client.post("/v1/commitments/lock", json=payload, headers=auth_headers(payload["members"][0]))


def join_commitment(client, auth_headers, invite_code, user_id):
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers(user_id)).status_code == 200
    return client.post(
        "/v1/commitments/join",
        json={"invite_code": invite_code},
        headers=auth_headers(user_id),
    )


def test_lock_endpoint_creates_commitment(client, auth_headers):
    payload = {
        "type": "rotating",
        "title": "Demo commitment",
        "vendor_id": "vendor_1",
        "contribution_amount": 2000,
        "contribution_frequency": "weekly",
        "cycles": 2,
        "members": ["user_1", "user_2"],
    }

    response = lock_commitment(client, auth_headers, payload)
    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "rotating"
    assert body["status"] == "pending_members"
    assert body["payout_schedule"][0]["cycle"] == 1
    assert body["payout_schedule"][0]["amount"] == 4000


def test_commitment_lifecycle_persists_and_advances_cycle(client, auth_headers):
    lock_payload = {
        "type": "rotating",
        "title": "Lifecycle commitment",
        "vendor_id": "vendor_lifecycle",
        "contribution_amount": 1500,
        "contribution_frequency": "weekly",
        "cycles": 2,
        "members": ["user_lifecycle_a", "user_lifecycle_b"],
    }

    lock_response = lock_commitment(client, auth_headers, lock_payload)
    assert lock_response.status_code == 201
    commitment_id = lock_response.json()["commitment_id"]

    join_response = join_commitment(client, auth_headers, lock_response.json()["invite_code"], "user_lifecycle_b")
    assert join_response.status_code == 200

    first_contribution = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1500, "event_id": "evt_lifecycle_a_1"},
        headers=auth_headers("user_lifecycle_a"),
    )
    assert first_contribution.status_code == 200
    first_body = first_contribution.json()
    assert first_body["completed_cycle"] is False
    assert first_body["status"] == "active"

    second_contribution = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1500, "event_id": "evt_lifecycle_b_1"},
        headers=auth_headers("user_lifecycle_b"),
    )
    assert second_contribution.status_code == 200
    second_body = second_contribution.json()
    assert second_body["completed_cycle"] is True
    assert second_body["beneficiary"]["user_id"] == "user_lifecycle_a"

    commitment_response = client.get(f"/v1/commitments/{commitment_id}", headers=auth_headers("user_lifecycle_a"))
    assert commitment_response.status_code == 200
    commitment_body = commitment_response.json()
    assert commitment_body["completed_cycle_count"] == 1
    assert commitment_body["current_cycle_number"] == 2
    assert commitment_body["cycle_states"][0]["status"] == "paid"


def test_unauthenticated_contribution_is_rejected(client, auth_headers):
    lock_response = lock_commitment(
        client,
        auth_headers,
        {
            "type": "rotating",
            "title": "Auth required",
            "vendor_id": "vendor_auth_required",
            "contribution_amount": 900,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["auth_a", "auth_b"],
        },
    )
    commitment_id = lock_response.json()["commitment_id"]
    assert join_commitment(client, auth_headers, lock_response.json()["invite_code"], "auth_b").status_code == 200

    response = client.post(f"/v1/commitments/{commitment_id}/contribute", json={"amount": 900, "event_id": "evt_unauthenticated"})
    assert response.status_code == 401


def test_contribution_actor_is_bound_to_authenticated_user(client, auth_headers):
    lock_response = lock_commitment(
        client,
        auth_headers,
        {
            "type": "rotating",
            "title": "Bound actor",
            "vendor_id": "vendor_actor",
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["member_a", "member_b"],
        },
    )
    commitment_id = lock_response.json()["commitment_id"]
    assert join_commitment(client, auth_headers, lock_response.json()["invite_code"], "member_b").status_code == 200

    response = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1000, "event_id": "evt_bound_actor", "user_id": "member_b"},
        headers=auth_headers("member_a"),
    )
    assert response.status_code == 200
    latest_contribution = response.json()["contributions"][-1]
    assert latest_contribution["user_id"] == "member_a"


def test_contribution_rejects_non_member(client, auth_headers):
    lock_response = lock_commitment(
        client,
        auth_headers,
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
    assert join_commitment(client, auth_headers, lock_response.json()["invite_code"], "member_b").status_code == 200

    response = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 900, "event_id": "evt_non_member"},
        headers=auth_headers("outsider"),
    )
    assert response.status_code == 403


def test_member_cannot_over_contribute_in_cycle(client, auth_headers):
    lock_response = lock_commitment(
        client,
        auth_headers,
        {
            "type": "rotating",
            "title": "Contribution guard",
            "vendor_id": "vendor_guard",
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["guard_a", "guard_b"],
        },
    )
    commitment_id = lock_response.json()["commitment_id"]
    assert join_commitment(client, auth_headers, lock_response.json()["invite_code"], "guard_b").status_code == 200

    first_response = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 600, "event_id": "evt_guard_partial"},
        headers=auth_headers("guard_a"),
    )
    assert first_response.status_code == 200

    second_response = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 500, "event_id": "evt_guard_over"},
        headers=auth_headers("guard_a"),
    )
    assert second_response.status_code == 400


def test_contribution_event_id_replays_without_a_second_charge(client, auth_headers):
    lock_response = lock_commitment(
        client,
        auth_headers,
        {
            "type": "rotating",
            "title": "Retry-safe contribution",
            "vendor_id": "vendor_idempotency",
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["retry_a", "retry_b"],
        },
    )
    commitment_id = lock_response.json()["commitment_id"]
    assert join_commitment(client, auth_headers, lock_response.json()["invite_code"], "retry_b").status_code == 200
    payload = {"amount": 1000, "event_id": "evt_retry_a_cycle_1"}

    first = client.post(
        f"/v1/commitments/{commitment_id}/contribute", json=payload, headers=auth_headers("retry_a")
    )
    assert first.status_code == 200
    assert first.json()["idempotent_replay"] is False

    replay = client.post(
        f"/v1/commitments/{commitment_id}/contribute", json=payload, headers=auth_headers("retry_a")
    )
    assert replay.status_code == 200
    assert replay.json()["idempotent_replay"] is True
    assert len(replay.json()["contributions"]) == 1


def test_contribution_event_id_cannot_be_reused_with_a_different_amount(client, auth_headers):
    lock_response = lock_commitment(
        client,
        auth_headers,
        {
            "type": "rotating",
            "title": "Retry conflict",
            "vendor_id": "vendor_idempotency_conflict",
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["retry_conflict_a", "retry_conflict_b"],
        },
    )
    commitment_id = lock_response.json()["commitment_id"]
    assert join_commitment(client, auth_headers, lock_response.json()["invite_code"], "retry_conflict_b").status_code == 200
    headers = auth_headers("retry_conflict_a")
    assert client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 600, "event_id": "evt_conflict"}, headers=headers,
    ).status_code == 200
    conflict = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 500, "event_id": "evt_conflict"}, headers=headers,
    )
    assert conflict.status_code == 409


def test_contribution_requires_an_event_id(client, auth_headers):
    lock_response = lock_commitment(
        client,
        auth_headers,
        {
            "type": "rotating",
            "title": "Event ID required",
            "vendor_id": "vendor_event_required",
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["event_a", "event_b"],
        },
    )
    assert join_commitment(client, auth_headers, lock_response.json()["invite_code"], "event_b").status_code == 200
    response = client.post(
        f"/v1/commitments/{lock_response.json()['commitment_id']}/contribute",
        json={"amount": 1000}, headers=auth_headers("event_a"),
    )
    assert response.status_code == 422


def test_unauthorized_user_cannot_verify_vendor(client, auth_headers):
    response = client.post(
        "/v1/vendors/verify",
        json={"vendor_id": "vendor_forbidden", "verified": True},
        headers=auth_headers("regular_user"),
    )
    assert response.status_code == 403


def test_vendor_verification_does_not_trust_verified_field(client, auth_headers):
    response = client.post(
        "/v1/vendors/verify",
        json={"vendor_id": "vendor_trust", "verified": False},
        headers=auth_headers("verifier_user", role="verifier"),
    )
    assert response.status_code == 200
    assert response.json()["verified"] is True


def test_0002_migration_downgrade_is_explicitly_irreversible():
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0002_contribution_engine_states.py"
    )
    spec = spec_from_file_location("migration_0002", migration_path)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    try:
        module.downgrade()
    except RuntimeError as exc:
        assert "irreversible" in str(exc)
    else:
        raise AssertionError("downgrade() should be explicitly irreversible.")
