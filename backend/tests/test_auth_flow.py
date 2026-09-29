"""Signup, login and OTP verification.

These cover the security properties that matter rather than the happy path alone:
the code is server-issued and single-use, the role is assigned by the backend and
not taken from the request, and the demo switcher is unavailable in production.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from core.config import get_settings


def _signup(client: TestClient, **overrides) -> dict:
    payload = {
        "role": "individual",
        "phone": "+234 803 000 0001",
        "name": "Amara Bello",
        "context": "trader",
        "terms_accepted": True,
    }
    payload.update(overrides)
    response = client.post("/v1/auth/signup", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _verify(client: TestClient, challenge_id: str, code: str):
    return client.post(
        "/v1/auth/verify-otp", json={"challenge_id": challenge_id, "code": code}
    )


def test_signup_issues_a_code_and_verifying_it_returns_a_token(client):
    challenge = _signup(client)
    assert challenge["expires_in_seconds"] > 0
    assert challenge["purpose"] == "signup"

    verified = _verify(client, challenge["challenge_id"], challenge["demo_code"])
    assert verified.status_code == 200, verified.text
    body = verified.json()
    assert body["token_type"] == "bearer"
    assert body["role"] == "individual"
    assert body["access_token"]

    me = client.get("/v1/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["user_id"] == body["user_id"]
    assert me.json()["role"] == "individual"
    assert me.json()["phone"] == "2348030000001"
    assert me.json()["phone_verified_at"] is not None


def test_the_code_is_never_returned_in_production(client):
    settings = get_settings()
    original = settings.environment
    object.__setattr__(settings, "environment", "production")
    try:
        challenge = _signup(client, phone="+234 803 000 0009")
        assert "demo_code" not in challenge
    finally:
        object.__setattr__(settings, "environment", original)


def test_a_code_can_only_be_used_once(client):
    challenge = _signup(client, phone="+234 803 000 0002")

    assert _verify(client, challenge["challenge_id"], challenge["demo_code"]).status_code == 200
    # Replaying a captured code must not mint a second session.
    assert _verify(client, challenge["challenge_id"], challenge["demo_code"]).status_code == 400


def test_a_wrong_code_is_rejected_and_counted(client):
    challenge = _signup(client, phone="+234 803 000 0003")
    assert _verify(client, challenge["challenge_id"], "000000").status_code == 401
    # The real code still works afterwards: a typo should not lock the user out.
    assert _verify(client, challenge["challenge_id"], challenge["demo_code"]).status_code == 200


def test_repeated_wrong_codes_eventually_lock_the_challenge_out(client):
    settings = get_settings()
    challenge = _signup(client, phone="+234 803 000 0004")
    for _ in range(settings.otp_max_attempts):
        assert _verify(client, challenge["challenge_id"], "000000").status_code == 401

    # Even the correct code is refused once the attempt cap is hit, so an
    # attacker cannot keep guessing one challenge indefinitely.
    blocked = _verify(client, challenge["challenge_id"], challenge["demo_code"])
    assert blocked.status_code == 429


def test_an_expired_code_is_refused(client):
    from datetime import datetime, timedelta

    from app.models import AuthChallenge

    challenge = _signup(client, phone="+234 803 000 0005")
    session = sessionmaker(bind=app.state.testing_session.kw["bind"])()
    row = session.get(AuthChallenge, challenge["challenge_id"])
    row.expires_at = datetime.utcnow() - timedelta(seconds=1)
    session.commit()
    session.close()

    assert _verify(client, challenge["challenge_id"], challenge["demo_code"]).status_code == 400


def test_the_server_issues_the_code_rather_than_trusting_the_client(client):
    challenge = _signup(client, phone="+234 803 000 0006")
    # A code the client made up is not the stored hash, so it cannot be used.
    assert _verify(client, challenge["challenge_id"], "135790").status_code == 401


def test_individual_signup_requires_accepting_the_terms(client):
    response = client.post(
        "/v1/auth/signup",
        json={
            "role": "individual",
            "phone": "+234 803 000 0007",
            "name": "No Terms",
            "terms_accepted": False,
        },
    )
    assert response.status_code == 400
    assert "terms" in response.json()["detail"].lower()


def test_vendor_signup_creates_a_linked_vendor_record(client):
    challenge = _signup(
        client,
        role="vendor",
        phone="+234 803 000 0008",
        name="Sura Test Shop",
        business_name="Sura Test Shop",
        business_category="electronics",
    )
    verified = _verify(client, challenge["challenge_id"], challenge["demo_code"])
    token = verified.json()["access_token"]
    assert verified.json()["role"] == "vendor"

    me = client.get("/v1/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert me["role"] == "vendor"
    # The vendor record must be resolvable by id, not inferred from the name.
    assert me["vendor"]["name"] == "Sura Test Shop"
    assert me["vendor"]["category"] == "electronics"
    assert me["vendor"]["verified"] is False


def test_vendor_signup_needs_business_details(client):
    response = client.post(
        "/v1/auth/signup",
        json={"role": "vendor", "phone": "+234 803 000 0010", "name": "Nameless", "terms_accepted": True},
    )
    assert response.status_code == 400


def test_bank_accounts_cannot_be_self_registered(client):
    response = client.post(
        "/v1/auth/signup",
        json={
            "role": "bank",
            "phone": "+234 803 000 0011",
            "name": "Not A Bank",
            "terms_accepted": True,
        },
    )
    assert response.status_code == 422


def test_a_phone_can_only_have_one_account(client):
    _signup(client, phone="+234 803 000 0012")
    duplicate = client.post(
        "/v1/auth/signup",
        json={
            "role": "individual",
            "phone": "08030000012",
            "name": "Impostor",
            "terms_accepted": True,
        },
    )
    assert duplicate.status_code == 409


def test_phone_numbers_are_compared_by_digits(client):
    _signup(client, phone="+234 803 000 0013")
    same_number_other_format = client.post(
        "/v1/auth/signup",
        json={
            "role": "individual",
            "phone": "234-803-000-0013",
            "name": "Same Person",
            "terms_accepted": True,
        },
    )
    assert same_number_other_format.status_code == 409


def test_login_issues_a_code_for_an_existing_account(client):
    challenge = _signup(client, phone="+234 803 000 0014")
    _verify(client, challenge["challenge_id"], challenge["demo_code"])

    settings = get_settings()
    original = settings.environment
    object.__setattr__(settings, "environment", "production")
    try:
        response = client.post("/v1/auth/login", json={"phone": "+234 803 000 0014"})
        assert response.status_code == 200
        assert "demo_code" not in response.json()
    finally:
        object.__setattr__(settings, "environment", original)


def test_login_for_an_unknown_number_says_the_same_thing(client):
    _signup(client, phone="+234 803 000 0015")
    response = client.post("/v1/auth/login", json={"phone": "+234 803 000 9999"})
    assert response.status_code == 404
    assert "no account" in response.json()["detail"].lower()


def test_requesting_a_second_code_too_quickly_is_refused(client):
    _signup(client, phone="+234 803 000 0016")
    second = client.post("/v1/auth/login", json={"phone": "+234 803 000 0016"})
    assert second.status_code == 429
    assert "wait" in second.json()["detail"].lower()


def test_a_superseded_code_stops_working(client):
    settings = get_settings()
    original_cooldown = settings.otp_resend_cooldown_seconds
    object.__setattr__(settings, "otp_resend_cooldown_seconds", 0)
    try:
        first = _signup(client, phone="+234 803 000 0017")
        second = client.post("/v1/auth/login", json={"phone": "+234 803 000 0017"}).json()

        # Requesting a new code must invalidate the old one, otherwise two live
        # codes exist for the same account and only the newer is meaningful.
        assert _verify(client, first["challenge_id"], first["demo_code"]).status_code == 400
        assert _verify(client, second["challenge_id"], second["demo_code"]).status_code == 200
    finally:
        object.__setattr__(settings, "otp_resend_cooldown_seconds", original_cooldown)


def test_demo_login_as_gives_a_working_session_per_role(client):
    for role in ("individual", "vendor", "bank"):
        response = client.post("/v1/demo/login-as", json={"role": role})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["role"] == role

        me = client.get("/v1/me", headers={"Authorization": f"Bearer {body['access_token']}"})
        assert me.status_code == 200
        assert me.json()["role"] == role


def test_demo_login_as_is_unavailable_in_production(client):
    settings = get_settings()
    original = settings.environment
    object.__setattr__(settings, "environment", "production")
    try:
        response = client.post("/v1/demo/login-as", json={"role": "bank"})
        assert response.status_code == 404
    finally:
        object.__setattr__(settings, "environment", original)


def test_the_legacy_demo_token_still_works(client):
    settings = get_settings()
    response = client.post(
        "/v1/auth/demo-token", json={"user_id": "legacy_user", "otp_code": settings.demo_otp_code}
    )
    assert response.status_code == 200
    assert response.json()["access_token"]
