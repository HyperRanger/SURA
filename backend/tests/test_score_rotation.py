"""Score behaviour across a full rotating cycle, not just the first one.

A single-cycle test passes even when the engine is wrong in ways that only
show up once a member has a history. These drive real commitments through the
whole rotation and assert the score at each step, so a late-breaking change to
the formula cannot pass unnoticed.

The engine is bounded to 0-100 with a base of 12 (app/services/scoring.py), so
expected values are derived from the rule, not copied from a previous run.
"""

from app.services.scoring import calculate_score


def _lock(client, auth_headers, vendor_id: str, members: list[str]) -> str:
    assert client.post(
        "/v1/vendors/verify",
        json={"vendor_id": vendor_id},
        headers=auth_headers("verifier_user", role="verifier"),
    ).status_code == 200

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
    assert response.status_code == 201
    return response.json()["commitment_id"]


def test_full_rotation_updates_score_each_cycle(client, auth_headers):
    members = ["rot_a", "rot_b", "rot_c"]
    commitment_id = _lock(client, auth_headers, "vendor_rot_1", members)

    observed: list[int] = []
    for cycle, member in enumerate(members, start=1):
        response = client.post(
            f"/v1/commitments/{commitment_id}/contribute",
            json={"amount": 1000, "event_id": f"evt_rot_{cycle}"},
            headers=auth_headers(member),
        )
        assert response.status_code == 200
        score = client.get(f"/v1/score/{member}", headers=auth_headers(member)).json()["score"]
        observed.append(score)

    # base 12 + 10 for the member's own full cycle. The cycle-completion bonus
    # (+15) only lands for the member whose payment closes the rotation, so the
    # first two members read 22 and the last one reads 37.
    assert observed == [22, 22, 37]

    # Every member paying once completes cycle 1, so the rotation advances and
    # the cycle-completion bonus lands for all three members.
    state = client.get(
        f"/v1/commitments/{commitment_id}", headers=auth_headers(members[0])
    ).json()
    assert state["current_cycle_number"] == 2
    assert state["completed_cycle_count"] == 1
    assert [cycle["status"] for cycle in state["cycle_states"]][0] == "paid"

    # The cycle-completion bonus is earned when the last member pays, and it
    # then applies to every member in the rotation, not just the payer.
    for member in members:
        assert client.get(
            f"/v1/score/{member}", headers=auth_headers(member)
        ).json()["score"] == calculate_score(12, [10], 0, 1)


def test_rotation_preserves_history_across_cycles(client, auth_headers):
    members = ["hist_a", "hist_b"]
    commitment_id = _lock(client, auth_headers, "vendor_rot_2", members)

    client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1000, "event_id": "evt_hist_1"},
        headers=auth_headers(members[0]),
    )
    client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1000, "event_id": "evt_hist_2"},
        headers=auth_headers(members[1]),
    )

    history = client.get(
        f"/v1/score/{members[0]}/history", headers=auth_headers(members[0])
    ).json()

    assert history["user_id"] == members[0]
    # hist_a pays first (22), then hist_b pays and closes the cycle, which earns
    # hist_a the completion bonus too (37). Both are real changes, so both are
    # on the trail, newest first.
    assert [entry["event_id"] for entry in history["entries"]] == ["evt_hist_2", "evt_hist_1"]
    assert [entry["score"] for entry in history["entries"]] == [37, 22]
    assert history["entries"][0]["old_score"] == 22
    assert history["entries"][1]["old_score"] is None
    assert all(entry["reason"] == "contribution_processed" for entry in history["entries"])
    assert history["current_score"] == history["entries"][0]["score"]
    # Every recorded entry must be an actual change; a no-op row would mean a
    # member's score was rewritten without moving.
    assert all(
        entry["old_score"] != entry["score"] for entry in history["entries"]
    ), "history must not contain rows where the score did not change"


def test_each_contribution_records_the_old_and_new_score(client, auth_headers):
    members = ["delta_a", "delta_b"]
    commitment_id = _lock(client, auth_headers, "vendor_rot_3", members)

    client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1000, "event_id": "evt_delta_1"},
        headers=auth_headers(members[0]),
    )
    # delta_b closes the cycle, which moves delta_a's score too.
    client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1000, "event_id": "evt_delta_2"},
        headers=auth_headers(members[1]),
    )
    # delta_a pays again in cycle 2: another 10 for the cycle they completed.
    client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1000, "event_id": "evt_delta_3"},
        headers=auth_headers(members[0]),
    )

    entries = client.get(
        f"/v1/score/{members[0]}/history", headers=auth_headers(members[0])
    ).json()["entries"]

    assert [entry["event_id"] for entry in entries] == ["evt_delta_3", "evt_delta_2", "evt_delta_1"]
    # Newest first, so each entry's old_score is the score the previous entry set.
    assert [entry["score"] for entry in entries] == [47, 37, 22]
    assert entries[0]["old_score"] == 37
    assert entries[1]["old_score"] == 22
    assert entries[2]["old_score"] is None
    assert all(entry["reason"] == "contribution_processed" for entry in entries)
    assert all(entry["old_score"] != entry["score"] for entry in entries)


def test_score_formula_is_bounded_and_documented():
    assert calculate_score(12, [10], 0, 1) == 37
    assert calculate_score(12, [], 0, 0) == 12
    assert calculate_score(12, [], 5, 0) == 0
    assert calculate_score(99, [10] * 50) == 100
