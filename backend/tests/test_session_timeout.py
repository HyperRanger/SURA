"""Automatic member logout after a period without activity.

A token is refused once the account has been quiet for the idle timeout, so a
forgotten tab cannot stay signed in forever. Any request slides the window, and
the activity stamp is throttled so an active member does not write on every
request.
"""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.models import User, Vendor
from core.config import get_settings
from core.security import create_token


def _signed_in_user(client: TestClient) -> dict:
    signup = client.post(
        "/v1/auth/signup",
        json={
            "role": "individual",
            "phone": "+234 803 000 0301",
            "name": "Idle Test User",
            "email": "member-2348030000301@example.test",
            "password": "correct-horse-battery-staple",
            "context": "student",
            "terms_accepted": True,
        },
    )
    assert signup.status_code == 201, signup.text
    verified = client.post(
        "/v1/auth/verify-otp",
        json={"challenge_id": signup.json()["challenge_id"], "code": signup.json()["demo_code"]},
    )
    assert verified.status_code == 200, verified.text
    return verified.json()


def _set_idle_timeout(seconds: int) -> int:
    settings = get_settings()
    previous = settings.session_idle_timeout_seconds
    object.__setattr__(settings, "session_idle_timeout_seconds", seconds)
    return previous


def test_a_signed_in_session_stamps_last_activity(client):
    verified = _signed_in_user(client)
    headers = {"Authorization": f"Bearer {verified['access_token']}"}

    assert client.get("/v1/me", headers=headers).status_code == 200

    db = client.app.state.testing_session()
    try:
        user = db.get(User, verified["user_id"])
        assert user is not None
        assert user.last_active_at is not None
    finally:
        db.close()


def test_otp_login_resets_a_previous_idle_timestamp(client):
    """A completed OTP login must not inherit an expired prior session."""
    verified = _signed_in_user(client)

    db = client.app.state.testing_session()
    try:
        user = db.get(User, verified["user_id"])
        assert user is not None
        user.last_active_at = datetime.utcnow() - timedelta(minutes=10)
        identifier = user.email
        db.commit()
    finally:
        db.close()

    login = client.post(
        "/v1/auth/login",
        json={"identifier": identifier, "password": "correct-horse-battery-staple"},
    )
    assert login.status_code == 200, login.text
    renewed = client.post(
        "/v1/auth/verify-otp",
        json={"challenge_id": login.json()["challenge_id"], "code": login.json()["demo_code"]},
    )
    assert renewed.status_code == 200, renewed.text

    me = client.get("/v1/me", headers={"Authorization": f"Bearer {renewed.json()['access_token']}"})
    assert me.status_code == 200, me.text


def test_an_idle_session_is_rejected(client):
    previous = _set_idle_timeout(60)
    try:
        verified = _signed_in_user(client)
        headers = {"Authorization": f"Bearer {verified['access_token']}"}
        assert client.get("/v1/me", headers=headers).status_code == 200

        db = client.app.state.testing_session()
        try:
            user = db.get(User, verified["user_id"])
            user.last_active_at = datetime.utcnow() - timedelta(seconds=120)
            db.commit()
        finally:
            db.close()

        expired = client.get("/v1/me", headers=headers)
        assert expired.status_code == 401
        assert "expired" in expired.json()["detail"].lower()
    finally:
        _set_idle_timeout(previous)


def test_an_idle_vendor_session_is_rejected(client):
    """The inactivity rule is shared by members and vendor sessions."""
    previous = _set_idle_timeout(60)
    try:
        db = client.app.state.testing_session()
        try:
            db.add(Vendor(id="idle_vendor_session_merchant", name="Idle Vendor Merchant", category="test"))
            vendor = User(
                id="idle_vendor_session_test",
                name="Idle Vendor Test",
                phone="2348030000399",
                role="vendor",
                vendor_id="idle_vendor_session_merchant",
                last_active_at=datetime.utcnow() - timedelta(seconds=120),
            )
            db.add(vendor)
            db.commit()
        finally:
            db.close()

        token = create_token("idle_vendor_session_test", {"role": "vendor"})
        expired = client.get("/v1/me", headers={"Authorization": f"Bearer {token}"})
        assert expired.status_code == 401
        assert "expired" in expired.json()["detail"].lower()
    finally:
        _set_idle_timeout(previous)


def test_activity_slides_the_window(client):
    previous = _set_idle_timeout(60)
    try:
        verified = _signed_in_user(client)
        headers = {"Authorization": f"Bearer {verified['access_token']}"}
        assert client.get("/v1/me", headers=headers).status_code == 200

        db = client.app.state.testing_session()
        try:
            user = db.get(User, verified["user_id"])
            user.last_active_at = datetime.utcnow() - timedelta(seconds=30)
            db.commit()
        finally:
            db.close()

        # Inside the window, the request is allowed and stamps activity.
        active = client.get("/v1/me", headers=headers)
        assert active.status_code == 200
    finally:
        _set_idle_timeout(previous)


def test_stamping_is_throttled_to_one_write_per_interval(client):
    verified = _signed_in_user(client)
    headers = {"Authorization": f"Bearer {verified['access_token']}"}

    assert client.get("/v1/me", headers=headers).status_code == 200
    db = client.app.state.testing_session()
    try:
        first = db.get(User, verified["user_id"]).last_active_at
    finally:
        db.close()

    assert client.get("/v1/me", headers=headers).status_code == 200
    db = client.app.state.testing_session()
    try:
        second = db.get(User, verified["user_id"]).last_active_at
    finally:
        db.close()

    # Two back-to-back requests happen well inside the stamp interval, so the
    # second one must not have rewritten the timestamp.
    assert first == second
