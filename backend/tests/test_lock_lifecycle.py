"""Acceptance tests for deadline, recovery, membership, and review-hold rules."""

from datetime import datetime, timedelta, timezone

from app.bank.models import BankPartner, BankStaff
from app.main import app
from app.models import Commitment, User


def _create_pending_lock(client, auth_headers, *, creator="lifecycle_creator", invitee="lifecycle_invitee"):
    assert client.post(
        "/v1/vendors/verify", json={"vendor_id": "lifecycle_vendor"},
        headers=auth_headers("lifecycle_verifier", role="verifier"),
    ).status_code == 200
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers(creator)).status_code == 200
    created = client.post(
        "/v1/commitments/lock",
        json={
            "type": "rotating", "title": "Lifecycle laptop", "vendor_id": "lifecycle_vendor",
            "contribution_amount": 1000, "contribution_frequency": "weekly", "cycles": 2,
            "members": [creator, invitee], "payout_order": [creator, invitee],
            "first_cycle_due_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        },
        headers=auth_headers(creator),
    )
    assert created.status_code == 201, created.text
    return created.json()


def test_deadline_drives_missed_state_and_full_recovery(client, auth_headers):
    created = _create_pending_lock(client, auth_headers)
    commitment_id = created["commitment_id"]
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers("lifecycle_invitee")).status_code == 200
    assert client.post("/v1/commitments/join", json={"invite_code": created["invite_code"]}, headers=auth_headers("lifecycle_invitee")).status_code == 200

    db = app.state.testing_session()
    try:
        commitment = db.get(Commitment, commitment_id)
        commitment.current_cycle_due_at = datetime.utcnow() - timedelta(hours=73)
        db.commit()
    finally:
        db.close()

    overdue = client.get(f"/v1/commitments/{commitment_id}", headers=auth_headers("lifecycle_creator"))
    assert overdue.status_code == 200
    assert overdue.json()["status"] == "missed"
    assert overdue.json()["missed_cycle_count"] == 1

    assert client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1000, "event_id": "lifecycle-a"}, headers=auth_headers("lifecycle_creator"),
    ).status_code == 200
    recovered = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1000, "event_id": "lifecycle-b"}, headers=auth_headers("lifecycle_invitee"),
    )
    assert recovered.status_code == 200
    assert recovered.json()["completed_cycle"] is True
    assert recovered.json()["status"] == "active"
    activity = client.get(f"/v1/commitments/{commitment_id}/activity", headers=auth_headers("lifecycle_creator")).json()
    assert "cycle_missed" in [event["event_type"] for event in activity]
    assert "cycle_recovered" in [event["event_type"] for event in activity]


def test_declined_invitation_can_be_replaced_only_before_activation(client, auth_headers):
    created = _create_pending_lock(client, auth_headers, creator="replace_creator", invitee="replace_old")
    commitment_id = created["commitment_id"]
    declined = client.post(f"/v1/commitments/{commitment_id}/decline", headers=auth_headers("replace_old"))
    assert declined.status_code == 200
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers("replace_new")).status_code == 200
    replaced = client.post(
        f"/v1/commitments/{commitment_id}/members/replace_old/replace",
        json={"replacement_user_id": "replace_new"}, headers=auth_headers("replace_creator"),
    )
    assert replaced.status_code == 200, replaced.text
    assert client.get(f"/v1/commitments/{commitment_id}", headers=auth_headers("replace_old")).status_code == 403
    joined = client.post("/v1/commitments/join", json={"invite_code": created["invite_code"]}, headers=auth_headers("replace_new"))
    assert joined.status_code == 200
    assert joined.json()["status"] == "active"


def test_bank_review_hold_pauses_and_then_restores_contributions(client, auth_headers):
    db = app.state.testing_session()
    try:
        db.add_all([
            BankPartner(id="lifecycle_bank", name="Lifecycle Bank"),
            User(id="case_creator", name="Case Creator", phone="234800001001", role="individual", bank_id="lifecycle_bank"),
            User(id="case_invitee", name="Case Invitee", phone="234800001002", role="individual", bank_id="lifecycle_bank"),
            User(id="case_staff_user", name="Case Staff", phone="234800001003", role="bank_admin", bank_id="lifecycle_bank"),
            BankStaff(id="case_staff", bank_id="lifecycle_bank", user_id="case_staff_user", email="case@bank.test", password_hash="unused", role="bank_admin", permissions_json="[]", mfa_phone="234800001003"),
        ])
        db.commit()
    finally:
        db.close()
    created = _create_pending_lock(client, auth_headers, creator="case_creator", invitee="case_invitee")
    commitment_id = created["commitment_id"]
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers("case_invitee")).status_code == 200
    assert client.post("/v1/commitments/join", json={"invite_code": created["invite_code"]}, headers=auth_headers("case_invitee")).status_code == 200
    bank_headers = auth_headers("case_staff_user", role="bank_admin", institution_id="lifecycle_bank")
    opened = client.post(f"/v1/bank/commitments/{commitment_id}/cases", json={"reason": "Member reported a dispute."}, headers=bank_headers)
    assert opened.status_code == 201, opened.text
    audit = client.get(f"/v1/bank/audit-log?commitment_id={commitment_id}", headers=bank_headers)
    assert audit.status_code == 200
    assert any(event["event_type"] == "commitment_case_opened" for event in audit.json())
    blocked = client.post(f"/v1/commitments/{commitment_id}/contribute", json={"amount": 1000, "event_id": "blocked"}, headers=auth_headers("case_creator"))
    assert blocked.status_code == 400
    resolved = client.post(f"/v1/bank/commitments/{commitment_id}/cases/{opened.json()['case_id']}/resolve", json={"note": "Reviewed; group may continue."}, headers=bank_headers)
    assert resolved.status_code == 200
    allowed = client.post(f"/v1/commitments/{commitment_id}/contribute", json={"amount": 1000, "event_id": "allowed"}, headers=auth_headers("case_creator"))
    assert allowed.status_code == 200


def test_bank_read_refreshes_an_elapsed_lock_deadline(client, auth_headers):
    db = app.state.testing_session()
    try:
        db.add_all([
            BankPartner(id="deadline_bank", name="Deadline Bank"),
            User(id="deadline_creator", name="Deadline Creator", phone="234800001101", role="individual", bank_id="deadline_bank"),
            User(id="deadline_invitee", name="Deadline Invitee", phone="234800001102", role="individual", bank_id="deadline_bank"),
            User(id="deadline_staff_user", name="Deadline Staff", phone="234800001103", role="bank_admin", bank_id="deadline_bank"),
            BankStaff(id="deadline_staff", bank_id="deadline_bank", user_id="deadline_staff_user", email="deadline@bank.test", password_hash="unused", role="bank_admin", permissions_json="[]", mfa_phone="234800001103"),
        ])
        db.commit()
    finally:
        db.close()
    created = _create_pending_lock(client, auth_headers, creator="deadline_creator", invitee="deadline_invitee")
    commitment_id = created["commitment_id"]
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers("deadline_invitee")).status_code == 200
    assert client.post("/v1/commitments/join", json={"invite_code": created["invite_code"]}, headers=auth_headers("deadline_invitee")).status_code == 200

    db = app.state.testing_session()
    try:
        db.get(Commitment, commitment_id).current_cycle_due_at = datetime.utcnow() - timedelta(hours=73)
        db.commit()
    finally:
        db.close()

    headers = auth_headers("deadline_staff_user", role="bank_admin", institution_id="deadline_bank")
    detail = client.get(f"/v1/bank/commitments/{commitment_id}", headers=headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["status"] == "missed"
