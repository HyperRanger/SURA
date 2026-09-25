from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_lock_endpoint_creates_commitment():
    payload = {
        "type": "rotating",
        "title": "Demo commitment",
        "vendor_id": "vendor_1",
        "contribution_amount": 2000,
        "contribution_frequency": "weekly",
        "cycles": 4,
        "members": ["user_1", "user_2"],
    }

    response = client.post("/v1/commitments/lock", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "rotating"
    assert body["status"] == "pending_members"
    assert len(body["payout_schedule"]) == 1
