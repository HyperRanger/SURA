"""Regression coverage for the documented rotating-Lock formation and miss policy."""

from datetime import datetime, timedelta, timezone

from app.main import app
from app.models import Commitment


def _active_lock(client, auth_headers, *, policy: str, prefix: str) -> tuple[str, str, str]:
    creator = f"{prefix}_creator"
    invitee = f"{prefix}_invitee"
    vendor = f"{prefix}_vendor"
    assert client.post(
        "/v1/vendors/verify", json={"vendor_id": vendor}, headers=auth_headers(f"{prefix}_verifier", role="verifier")
    ).status_code == 200
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers(creator)).status_code == 200
    created = client.post(
        "/v1/commitments/lock",
        json={
            "type": "rotating",
            "title": "Policy coverage",
            "vendor_id": vendor,
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": [creator, invitee],
            "payout_order": [creator, invitee],
            "missed_cycle_policy": policy,
            "first_cycle_due_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        },
        headers=auth_headers(creator),
    )
    assert created.status_code == 201, created.text
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers(invitee)).status_code == 200
    assert client.post(
        "/v1/commitments/join",
        json={"invite_code": created.json()["invite_code"]},
        headers=auth_headers(invitee),
    ).status_code == 200
    return created.json()["commitment_id"], creator, invitee


def test_rotating_lock_requires_two_final_members(client, auth_headers):
    assert client.post(
        "/v1/vendors/verify", json={"vendor_id": "minimum_vendor"}, headers=auth_headers("minimum_verifier", role="verifier")
    ).status_code == 200
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers("minimum_creator")).status_code == 200
    response = client.post(
        "/v1/commitments/lock",
        json={
            "type": "rotating", "title": "One is not a group", "vendor_id": "minimum_vendor",
            "contribution_amount": 1000, "contribution_frequency": "weekly", "cycles": 1,
            "members": ["minimum_creator"], "payout_order": ["minimum_creator"],
        },
        headers=auth_headers("minimum_creator"),
    )
    assert response.status_code == 400
    assert "at least two distinct members" in response.json()["detail"]


def test_cover_shortfall_is_persisted_and_can_complete_a_missed_pool(client, auth_headers):
    commitment_id, creator, _ = _active_lock(client, auth_headers, policy="cover_shortfall", prefix="cover")
    assert client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1000, "event_id": "cover-own"}, headers=auth_headers(creator),
    ).status_code == 200

    db = app.state.testing_session()
    try:
        db.get(Commitment, commitment_id).current_cycle_due_at = datetime.utcnow() - timedelta(hours=73)
        db.commit()
    finally:
        db.close()

    missed = client.get(f"/v1/commitments/{commitment_id}", headers=auth_headers(creator))
    assert missed.status_code == 200
    assert missed.json()["status"] == "missed"
    assert missed.json()["missed_cycle_policy"] == "cover_shortfall"
    covered = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1000, "event_id": "cover-gap"}, headers=auth_headers(creator),
    )
    assert covered.status_code == 200, covered.text
    assert covered.json()["completed_cycle"] is True
    assert covered.json()["contribution_status"] == "shortfall_cover"


def test_cancel_and_refund_records_simulated_bank_instruction(client, auth_headers):
    commitment_id, creator, _ = _active_lock(client, auth_headers, policy="cancel_and_refund", prefix="refund")
    db = app.state.testing_session()
    try:
        db.get(Commitment, commitment_id).current_cycle_due_at = datetime.utcnow() - timedelta(hours=73)
        db.commit()
    finally:
        db.close()

    detail = client.get(f"/v1/commitments/{commitment_id}", headers=auth_headers(creator))
    assert detail.status_code == 200
    assert detail.json()["status"] == "cancelled"
    activity = client.get(f"/v1/commitments/{commitment_id}/activity", headers=auth_headers(creator))
    assert activity.status_code == 200
    assert "refund_instruction_created" in [event["event_type"] for event in activity.json()]


def test_demo_grace_period_is_fixed_at_72_hours(client, auth_headers):
    response = client.post(
        "/v1/commitments/lock",
        json={"title": "Invalid grace", "vendor_id": "unused", "contribution_amount": 1000,
              "contribution_frequency": "weekly", "cycles": 2, "members": ["one", "two"],
              "grace_period_hours": 48},
        headers=auth_headers("one"),
    )
    assert response.status_code == 422
