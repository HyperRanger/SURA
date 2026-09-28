from sqlalchemy.orm import Query

from app.services.payout_rules import apply_anchor_and_cap_rule, build_payout_schedule


def test_build_payout_schedule_is_deterministic():
    schedule = build_payout_schedule(["member_a", "member_b", "member_c"], 1500, 3)
    assert schedule == [
        {"cycle": 1, "beneficiary_id": "member_a", "amount": 4500},
        {"cycle": 2, "beneficiary_id": "member_b", "amount": 4500},
        {"cycle": 3, "beneficiary_id": "member_c", "amount": 4500},
    ]


def test_build_payout_schedule_is_empty_without_members():
    assert build_payout_schedule([], 1500, 3) == []


def test_apply_anchor_and_cap_rule_caps_first_cycle_for_genesis_groups():
    capped = apply_anchor_and_cap_rule(25000, 1)
    unchanged = apply_anchor_and_cap_rule(25000, 2)
    assert capped == 10000
    assert unchanged == 25000


def test_contribution_flow_uses_row_lock(client, auth_headers, monkeypatch):
    lock_called = {"value": False}
    original = Query.with_for_update

    def wrapped(self, *args, **kwargs):
        lock_called["value"] = True
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Query, "with_for_update", wrapped)

    assert client.post(
        "/v1/vendors/verify",
        json={"vendor_id": "vendor_lock"},
        headers=auth_headers("verifier_user", role="verifier"),
    ).status_code == 200
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers("lock_a")).status_code == 200
    lock_response = client.post(
        "/v1/commitments/lock",
        json={
            "type": "rotating",
            "title": "Row lock",
            "vendor_id": "vendor_lock",
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["lock_a", "lock_b"],
            "payout_order": ["lock_a", "lock_b"],
        },
        headers=auth_headers("lock_a"),
    )
    commitment_id = lock_response.json()["commitment_id"]
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers("lock_b")).status_code == 200
    assert client.post(
        "/v1/commitments/join",
        json={"invite_code": lock_response.json()["invite_code"]},
        headers=auth_headers("lock_b"),
    ).status_code == 200

    response = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1000, "event_id": "evt_row_lock_1"},
        headers=auth_headers("lock_a"),
    )
    assert response.status_code == 200
    assert lock_called["value"] is True
