from datetime import datetime

from app.models import ScoreHistory, User


def test_lock_event_persists_an_explainable_five_pillar_score(client, auth_headers):
    db = client.app.state.testing_session()
    try:
        db.add(User(id="score_creator", name="Score Creator", phone="score-creator@sura.local", verified_at=datetime.utcnow()))
        db.commit()
    finally:
        db.close()

    assert client.post(
        "/v1/vendors/verify",
        json={"vendor_id": "score_vendor"},
        headers=auth_headers("verifier", role="verifier"),
    ).status_code == 200
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers("score_creator")).status_code == 200
    created = client.post(
        "/v1/commitments/lock",
        json={
            "type": "rotating",
            "title": "Scored Lock",
            "vendor_id": "score_vendor",
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["score_creator", "score_member"],
            "payout_order": ["score_creator", "score_member"],
        },
        headers=auth_headers("score_creator"),
    )
    assert created.status_code == 201
    commitment_id = created.json()["commitment_id"]
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers("score_member")).status_code == 200
    assert client.post(
        "/v1/commitments/join",
        json={"invite_code": created.json()["invite_code"]},
        headers=auth_headers("score_member"),
    ).status_code == 200
    for user_id in ("score_creator", "score_member"):
        assert client.post(
            f"/v1/commitments/{commitment_id}/contribute",
            json={"amount": 1000, "event_id": f"evt_{user_id}_one"},
            headers=auth_headers(user_id),
        ).status_code == 200

    db = client.app.state.testing_session()
    try:
        snapshot = db.query(ScoreHistory).filter(ScoreHistory.user_id == "score_creator").order_by(ScoreHistory.computed_at.desc()).first()
        assert snapshot is not None
        assert snapshot.score == 295
        assert snapshot.score_before == 120
        assert snapshot.event_type == "contribution_processed"
        assert snapshot.score_version == "trd-5.2-v1"
        assert snapshot.signals_json is not None
    finally:
        db.close()

    response = client.get("/v1/score/score_creator", headers=auth_headers("score_creator"))
    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 295
    assert body["tier"] == "entry"
    assert body["breakdown"] == {
        "commitment_behaviour": 175,
        "repayment_behaviour": 0,
        "transaction_stability": 0,
        "institutional_verification": 120,
        "social_reliability": 0,
    }
    assert body["score_version"] == "trd-5.2-v1"

    assert client.get("/v1/score/score_creator", headers=auth_headers("score_member")).status_code == 403
