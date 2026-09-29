"""Regression tests for contribute idempotency against the live engine.

A retried or double-fired contribute must never double-count. The real
`record_contribution` guards this by matching an existing Contribution row on
`event_id`, so these tests drive the HTTP endpoint rather than a mock to prove
the guard holds end to end.
"""


def _lock_commitment(client, auth_headers, vendor_id: str, member: str) -> str:
    assert client.post(
        "/v1/vendors/verify",
        json={"vendor_id": vendor_id},
        headers=auth_headers("verifier_user", role="verifier"),
    ).status_code == 200
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers(member)).status_code == 200

    response = client.post(
        "/v1/commitments/lock",
        json={
            "type": "rotating",
            "title": "Replay guard",
            "vendor_id": vendor_id,
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 1,
            "members": [member],
            "payout_order": [member],
        },
        headers=auth_headers(member),
    )
    assert response.status_code == 201
    return response.json()["commitment_id"]


def test_replayed_event_id_does_not_double_count(client, auth_headers):
    commitment_id = _lock_commitment(client, auth_headers, "vendor_replay_1", "replay_a")
    payload = {"amount": 1000, "event_id": "evt_replay_1"}
    headers = auth_headers("replay_a")

    first = client.post(f"/v1/commitments/{commitment_id}/contribute", json=payload, headers=headers)
    replay = client.post(f"/v1/commitments/{commitment_id}/contribute", json=payload, headers=headers)

    assert first.status_code == 200
    assert replay.status_code == 200
    assert first.json().get("idempotent_replay") is not True
    assert replay.json()["idempotent_replay"] is True
    assert replay.json()["event_id"] == "evt_replay_1"
    assert len(replay.json()["contributions"]) == 1


def test_replay_leaves_score_history_unchanged(client, auth_headers):
    commitment_id = _lock_commitment(client, auth_headers, "vendor_replay_2", "replay_b")
    payload = {"amount": 1000, "event_id": "evt_replay_2"}
    headers = auth_headers("replay_b")

    client.post(f"/v1/commitments/{commitment_id}/contribute", json=payload, headers=headers)
    after_first = client.get("/v1/score/replay_b", headers=headers).json()["score"]
    client.post(f"/v1/commitments/{commitment_id}/contribute", json=payload, headers=headers)
    after_replay = client.get("/v1/score/replay_b", headers=headers).json()["score"]

    assert after_replay == after_first


def test_reused_event_id_with_different_amount_is_rejected(client, auth_headers):
    commitment_id = _lock_commitment(client, auth_headers, "vendor_replay_3", "replay_c")
    headers = auth_headers("replay_c")

    client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 500, "event_id": "evt_replay_3"},
        headers=headers,
    )
    conflict = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1000, "event_id": "evt_replay_3"},
        headers=headers,
    )

    assert conflict.status_code == 409
