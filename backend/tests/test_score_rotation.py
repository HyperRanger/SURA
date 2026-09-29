"""Integration coverage for score updates across a real rotating Lock cycle."""


def _lock_and_join(client, auth_headers, vendor_id: str, members: list[str]) -> str:
    assert client.post(
        "/v1/vendors/verify",
        json={"vendor_id": vendor_id},
        headers=auth_headers("verifier", role="verifier"),
    ).status_code == 200
    for member in members:
        assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers(member)).status_code == 200
    response = client.post(
        "/v1/commitments/lock",
        json={
            "type": "rotating",
            "title": "Full rotation",
            "vendor_id": vendor_id,
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": len(members),
            "members": members,
            "payout_order": members,
        },
        headers=auth_headers(members[0]),
    )
    assert response.status_code == 201, response.text
    for member in members[1:]:
        joined = client.post(
            "/v1/commitments/join",
            json={"invite_code": response.json()["invite_code"]},
            headers=auth_headers(member),
        )
        assert joined.status_code == 200, joined.text
    return response.json()["commitment_id"]


def test_full_rotation_advances_cycle_and_records_explainable_scores(client, auth_headers):
    members = ["rot_a", "rot_b", "rot_c"]
    commitment_id = _lock_and_join(client, auth_headers, "vendor_rot_1", members)

    for cycle, member in enumerate(members, start=1):
        response = client.post(
            f"/v1/commitments/{commitment_id}/contribute",
            json={"amount": 1000, "event_id": f"evt_rot_{cycle}"},
            headers=auth_headers(member),
        )
        assert response.status_code == 200, response.text

    state = client.get(f"/v1/commitments/{commitment_id}", headers=auth_headers(members[0])).json()
    assert state["current_cycle_number"] == 2
    assert state["completed_cycle_count"] == 1
    assert state["cycle_states"][0]["status"] == "paid"

    for member in members:
        score = client.get(f"/v1/score/{member}", headers=auth_headers(member)).json()
        assert score["score"] == 175
        assert score["breakdown"]["commitment_behaviour"] == 175
        history = client.get(f"/v1/score/{member}/history", headers=auth_headers(member)).json()
        assert history["entries"][0]["event_type"] == "contribution_processed"
        assert history["entries"][0]["source_id"] == "evt_rot_3"


def test_score_history_only_records_actual_score_changes(client, auth_headers):
    members = ["hist_a", "hist_b"]
    commitment_id = _lock_and_join(client, auth_headers, "vendor_rot_2", members)
    for index, member in enumerate(members, start=1):
        assert client.post(
            f"/v1/commitments/{commitment_id}/contribute",
            json={"amount": 1000, "event_id": f"evt_hist_{index}"},
            headers=auth_headers(member),
        ).status_code == 200

    history = client.get("/v1/score/hist_a/history", headers=auth_headers("hist_a")).json()
    assert [entry["score"] for entry in history["entries"]] == [175, 0]
    assert history["entries"][0]["score_before"] == 0
    assert history["entries"][0]["source_id"] == "evt_hist_2"
    assert all(
        entry["score_before"] is None or entry["score_before"] != entry["score"]
        for entry in history["entries"]
    )
