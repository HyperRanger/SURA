"""Restart-survival proof for the Durability layer.

The suite normally pins the database to in-memory SQLite (StaticPool), which
can carry unflushed state on a single connection and therefore cannot prove the
property that actually matters to a production demo: once an event has been
processed and committed, a later process must not re-process it, and its
history must still be queryable. This test drives the real HTTP contribute
flow against a file-backed SQLite database, then discards the engine and
sessions entirely and opens a brand-new engine over the same file — the closest
in-process equivalent to a process restart — before asserting the guard still
holds.
"""

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Contribution, ScoreHistory


def _file_client(db_file: Path) -> TestClient:
    engine = create_engine(f"sqlite+pysqlite:///{db_file.as_posix()}")
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    app.state.testing_session = testing_session
    app.state.testing_engine = engine

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _teardown_client() -> None:
    app.dependency_overrides.clear()
    engine = app.state.testing_engine
    del app.state.testing_engine
    del app.state.testing_session
    engine.dispose()


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
            "title": "Restart guard",
            "vendor_id": vendor_id,
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": [member, f"{member}_partner"],
            "payout_order": [member, f"{member}_partner"],
        },
        headers=auth_headers(member),
    )
    assert response.status_code == 201
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers(f"{member}_partner")).status_code == 200
    assert client.post(
        "/v1/commitments/join",
        json={"invite_code": response.json()["invite_code"]},
        headers=auth_headers(f"{member}_partner"),
    ).status_code == 200
    return response.json()["commitment_id"]


def test_processed_event_survives_restart(tmp_path, auth_headers):
    db_file = tmp_path / "sura_restart.db"

    client = _file_client(db_file)
    try:
        commitment_id = _lock_commitment(client, auth_headers, "vendor_restart_1", "restart_a")
        payload = {"amount": 1000, "event_id": "evt_restart_1"}
        headers = auth_headers("restart_a")
        first = client.post(f"/v1/commitments/{commitment_id}/contribute", json=payload, headers=headers)
        assert first.status_code == 200
        assert first.json().get("idempotent_replay") is not True
    finally:
        _teardown_client()

    restarted = _file_client(db_file)
    try:
        replay = restarted.post(f"/v1/commitments/{commitment_id}/contribute", json=payload, headers=headers)
        assert replay.status_code == 200
        assert replay.json()["idempotent_replay"] is True
        assert replay.json()["event_id"] == "evt_restart_1"
        assert len(replay.json()["contributions"]) == 1
    finally:
        _teardown_client()


def test_score_trail_survives_restart(tmp_path, auth_headers):
    db_file = tmp_path / "sura_restart_score.db"

    client = _file_client(db_file)
    try:
        commitment_id = _lock_commitment(client, auth_headers, "vendor_restart_2", "restart_b")
        payload = {"amount": 1000, "event_id": "evt_restart_2"}
        headers = auth_headers("restart_b")
        client.post(f"/v1/commitments/{commitment_id}/contribute", json=payload, headers=headers)
    finally:
        _teardown_client()

    engine = create_engine(f"sqlite+pysqlite:///{db_file.as_posix()}")
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        assert db.query(Contribution).filter(Contribution.event_id == "evt_restart_2").count() == 1
        contributions = db.query(ScoreHistory).filter(ScoreHistory.event_type == "contribution_processed").count()
        assert contributions >= 1
    finally:
        db.close()
        engine.dispose()