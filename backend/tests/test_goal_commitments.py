"""End-to-end rules for the two non-rotating, target-based commitments."""


def _verify_vendor(client, auth_headers, vendor_id: str) -> None:
    response = client.post(
        "/v1/vendors/verify",
        json={"vendor_id": vendor_id},
        headers=auth_headers("goal_verifier", role="verifier"),
    )
    assert response.status_code == 200, response.text


def _consent(client, auth_headers, user_id: str) -> None:
    response = client.post("/v1/consent", json={"granted": True}, headers=auth_headers(user_id))
    assert response.status_code == 200, response.text


def test_individual_goal_accumulates_to_target_and_issues_one_voucher(client, auth_headers):
    _verify_vendor(client, auth_headers, "vendor_goal_individual")
    _consent(client, auth_headers, "goal_owner")
    created = client.post(
        "/v1/commitments/lock",
        json={
            "type": "individual_goal", "title": "Laptop target", "vendor_id": "vendor_goal_individual",
            "contribution_amount": 5_000, "target_amount": 12_000, "contribution_frequency": "monthly",
            "cycles": 1, "members": [], "payout_order": [],
        }, headers=auth_headers("goal_owner"),
    )
    assert created.status_code == 201, created.text
    commitment_id = created.json()["commitment_id"]
    assert created.json()["status"] == "active"

    first = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 5_000, "event_id": "goal-individual-1"}, headers=auth_headers("goal_owner"),
    )
    assert first.status_code == 200, first.text
    assert first.json()["goal"]["remaining_total"] == 7_000
    assert first.json()["status"] == "active"

    replay = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 5_000, "event_id": "goal-individual-1"}, headers=auth_headers("goal_owner"),
    )
    assert replay.status_code == 200, replay.text
    assert replay.json()["idempotent_replay"] is True
    assert replay.json()["goal"]["contributed_total"] == 5_000

    over = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 8_000, "event_id": "goal-individual-over"}, headers=auth_headers("goal_owner"),
    )
    assert over.status_code == 400
    assert "remaining goal target" in over.json()["detail"]

    complete = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 7_000, "event_id": "goal-individual-2"}, headers=auth_headers("goal_owner"),
    )
    assert complete.status_code == 200, complete.text
    assert complete.json()["status"] == "completed"
    assert complete.json()["goal"]["progress_percent"] == 100
    voucher = client.get(f"/v1/commitments/{commitment_id}/cycles/1/voucher", headers=auth_headers("goal_owner"))
    assert voucher.status_code == 200, voucher.text
    assert voucher.json()["amount"] == 12_000
    assert voucher.json()["status"] == "ready"


def test_collective_goal_requires_joining_and_pays_nominated_beneficiary(client, auth_headers):
    _verify_vendor(client, auth_headers, "vendor_goal_collective")
    _consent(client, auth_headers, "goal_creator")
    created = client.post(
        "/v1/commitments/lock",
        json={
            "type": "collective_goal", "title": "Studio equipment", "vendor_id": "vendor_goal_collective",
            "contribution_amount": 2_000, "target_amount": 6_000, "contribution_frequency": "weekly",
            "cycles": 1, "members": ["goal_friend"], "beneficiary_id": "goal_friend", "payout_order": [],
        }, headers=auth_headers("goal_creator"),
    )
    assert created.status_code == 201, created.text
    commitment_id = created.json()["commitment_id"]
    assert created.json()["status"] == "pending_members"

    _consent(client, auth_headers, "goal_friend")
    joined = client.post("/v1/commitments/join", json={"invite_code": created.json()["invite_code"]}, headers=auth_headers("goal_friend"))
    assert joined.status_code == 200, joined.text
    assert joined.json()["status"] == "active"

    for user_id, amount, event_id in (("goal_creator", 2_500, "goal-group-1"), ("goal_friend", 3_500, "goal-group-2")):
        contributed = client.post(
            f"/v1/commitments/{commitment_id}/contribute",
            json={"amount": amount, "event_id": event_id}, headers=auth_headers(user_id),
        )
        assert contributed.status_code == 200, contributed.text

    denied = client.get(f"/v1/commitments/{commitment_id}/cycles/1/voucher", headers=auth_headers("goal_creator"))
    assert denied.status_code == 403
    voucher = client.get(f"/v1/commitments/{commitment_id}/cycles/1/voucher", headers=auth_headers("goal_friend"))
    assert voucher.status_code == 200, voucher.text
    assert voucher.json()["amount"] == 6_000
