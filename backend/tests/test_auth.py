def test_demo_token_issues_a_token_for_the_online_demo(client):
    response = client.post("/v1/auth/demo-token", json={"user_id": "usr_demo_amara", "otp_code": "123456"})
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_demo_token_rejects_an_invalid_otp(client):
    response = client.post("/v1/auth/demo-token", json={"user_id": "usr_demo_amara", "otp_code": "wrong"})
    assert response.status_code == 401


def test_lock_and_score_routes_require_authentication(client):
    lock_response = client.post(
        "/v1/commitments/lock",
        json={
            "type": "rotating", "title": "Protected lock", "vendor_id": "vendor_missing",
            "contribution_amount": 1000, "contribution_frequency": "weekly", "cycles": 1,
            "members": ["auth_member"], "payout_order": ["auth_member"],
        },
    )
    assert lock_response.status_code == 401
    assert client.get("/v1/score/auth_member").status_code == 401
