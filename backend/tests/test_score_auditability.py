"""Phase B acceptance tests for private, versioned Score evidence."""

from datetime import datetime

from app.main import app
from app.models import AccountActivitySignal, ScoreHistory, User
from app.services.score_service import record_score_snapshot


def test_member_can_open_one_immutable_score_history_entry(client, auth_headers):
    db = app.state.testing_session()
    try:
        db.add(User(id="score_audit_member", name="Score Audit Member", phone="234800002000"))
        db.commit()
    finally:
        db.close()

    assert client.post(
        "/v1/consent", json={"granted": True}, headers=auth_headers("score_audit_member")
    ).status_code == 200

    history = client.get(
        "/v1/score/score_audit_member/history", headers=auth_headers("score_audit_member")
    )
    assert history.status_code == 200, history.text
    entry = history.json()["entries"][0]
    assert entry["id"]
    assert entry["event_type"] == "score_consent_granted"
    assert entry["score_version"] == "trd-5.2-v1"
    assert set(entry["signals"]) >= {"locks_joined", "contributions_due", "institution_verified"}
    assert set(entry["weights"]) == {
        "commitment_behaviour",
        "repayment_behaviour",
        "transaction_stability",
        "institutional_verification",
        "social_reliability",
    }

    detail = client.get(
        f"/v1/score/score_audit_member/history/{entry['id']}",
        headers=auth_headers("score_audit_member"),
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["id"] == entry["id"]
    assert detail.json()["computed_at"] == entry["computed_at"]
    assert client.get(
        f"/v1/score/score_audit_member/history/{entry['id']}",
        headers=auth_headers("another_member"),
    ).status_code == 403


def test_withdrawn_consent_prevents_new_score_snapshots(client, auth_headers):
    db = app.state.testing_session()
    try:
        db.add(User(id="consent_withdrawn", name="Consent Withdrawn", phone="234800002001"))
        db.commit()
    finally:
        db.close()

    assert client.post(
        "/v1/consent", json={"granted": True}, headers=auth_headers("consent_withdrawn")
    ).status_code == 200
    assert client.post(
        "/v1/consent", json={"granted": False}, headers=auth_headers("consent_withdrawn")
    ).status_code == 200

    db = app.state.testing_session()
    try:
        db.add(AccountActivitySignal(
            id="withdrawn_activity", user_id="consent_withdrawn", source="test", occurred_at=datetime.utcnow()
        ))
        assert record_score_snapshot(
            db,
            "consent_withdrawn",
            event_type="test_event",
            reason="This must not be processed after withdrawal.",
            source_id="withdrawn_activity",
        ) is None
        db.commit()
        assert db.query(ScoreHistory).filter(ScoreHistory.user_id == "consent_withdrawn").count() == 1
    finally:
        db.close()
