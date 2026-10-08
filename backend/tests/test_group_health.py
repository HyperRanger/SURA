"""Phase F group-health contract tests."""

from datetime import datetime, timedelta

from app.models import Commitment, CommitmentBeneficiary
from app.services.demo_data import DEMO_BANK_ID, DEMO_COMMITMENT_ID, seed_demo_data


def _seed(client) -> None:
    db = client.app.state.testing_session()
    try:
        seed_demo_data(db, reset=True)
        db.commit()
    finally:
        db.close()


def test_member_group_health_is_aggregate_advisory_and_member_scoped(client, auth_headers):
    _seed(client)

    response = client.get(
        f"/v1/app/commitments/{DEMO_COMMITMENT_ID}/group-health",
        headers=auth_headers("usr_demo_amara"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["advisory"] is True
    assert body["group_health"] == "low_risk"
    assert body["confidence"] == "moderate"
    assert body["metrics"]["completed_cycles"] == 1
    assert body["metrics"]["current_cycle_unpaid_member_count"] == 1
    assert body["metrics"]["current_cycle_deadline_state"] == "active"
    assert body["unavailable_signals"] == [
        "external payment-rail settlement",
        "member exit reason",
    ]
    assert "user_id" not in body["metrics"]

    denied = client.get(
        f"/v1/app/commitments/{DEMO_COMMITMENT_ID}/group-health",
        headers=auth_headers("someone_else"),
    )
    assert denied.status_code == 403


def test_missed_cycle_is_high_risk_and_bank_receives_same_aggregate_report(client, auth_headers):
    _seed(client)
    db = client.app.state.testing_session()
    try:
        commitment = db.get(Commitment, DEMO_COMMITMENT_ID)
        commitment.status = "missed"
        second_cycle = (
            db.query(CommitmentBeneficiary)
            .filter(
                CommitmentBeneficiary.commitment_id == DEMO_COMMITMENT_ID,
                CommitmentBeneficiary.cycle_number == 2,
            )
            .one()
        )
        second_cycle.status = "missed"
        db.commit()
    finally:
        db.close()

    member_report = client.get(
        f"/v1/app/commitments/{DEMO_COMMITMENT_ID}/group-health",
        headers=auth_headers("usr_demo_amara"),
    )
    bank_report = client.get(
        f"/v1/bank/commitments/{DEMO_COMMITMENT_ID}/group-health",
        headers=auth_headers("health_bank_admin", role="bank_admin", institution_id=DEMO_BANK_ID),
    )

    assert member_report.status_code == 200, member_report.text
    assert bank_report.status_code == 200, bank_report.text
    assert member_report.json()["group_health"] == "high_risk"
    assert member_report.json()["metrics"]["missed_cycles"] == 1
    assert bank_report.json() == member_report.json()


def test_deadline_state_is_explainable_without_changing_the_lock(client, auth_headers):
    _seed(client)
    db = client.app.state.testing_session()
    try:
        commitment = db.get(Commitment, DEMO_COMMITMENT_ID)
        commitment.current_cycle_due_at = datetime.utcnow() - timedelta(hours=1)
        commitment.grace_period_hours = 72
        db.commit()
    finally:
        db.close()

    overdue = client.get(
        f"/v1/app/commitments/{DEMO_COMMITMENT_ID}/group-health",
        headers=auth_headers("usr_demo_amara"),
    )
    assert overdue.status_code == 200, overdue.text
    assert overdue.json()["group_health"] == "medium_risk"
    assert overdue.json()["metrics"]["current_cycle_deadline_state"] == "overdue"
    assert overdue.json()["metrics"]["current_cycle_due_at"] is not None

    db = client.app.state.testing_session()
    try:
        commitment = db.get(Commitment, DEMO_COMMITMENT_ID)
        commitment.current_cycle_due_at = datetime.utcnow() - timedelta(hours=73)
        db.commit()
    finally:
        db.close()

    overdue_grace = client.get(
        f"/v1/app/commitments/{DEMO_COMMITMENT_ID}/group-health",
        headers=auth_headers("usr_demo_amara"),
    )
    assert overdue_grace.status_code == 200, overdue_grace.text
    assert overdue_grace.json()["group_health"] == "high_risk"
    assert overdue_grace.json()["metrics"]["current_cycle_deadline_state"] == "missed"
