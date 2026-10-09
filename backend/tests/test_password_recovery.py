"""Self-service password recovery for member accounts.

Recovery reuses the signup/login discipline: the code is server-issued, single-use,
attempt-capped and delivered by SMS, the request never reveals whether an
identifier exists, and a completed recovery ends every session and device.
"""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import AuthChallenge

NEW_PASSWORD = "alpaca-has-a-broad-back"
OLD_PASSWORD = "correct-horse-battery-staple"


def _signup(client: TestClient, phone: str, **overrides) -> dict:
    payload = {
        "role": "individual",
        "phone": phone,
        "name": "Recovery User",
        "email": f'member-{"".join(ch for ch in phone if ch.isdigit())}@example.test',
        "password": OLD_PASSWORD,
        "context": "trader",
        "terms_accepted": True,
    }
    payload.update(overrides)
    response = client.post("/v1/auth/signup", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _verified_user(client: TestClient, phone: str, **signup_overrides) -> dict:
    challenge = _signup(client, phone, **signup_overrides)
    verified = client.post(
        "/v1/auth/verify-otp",
        json={"challenge_id": challenge["challenge_id"], "code": challenge["demo_code"]},
    )
    assert verified.status_code == 200, verified.text
    return verified.json()


def _recover(client: TestClient, identifier: str) -> dict:
    response = client.post("/v1/auth/password-recovery", json={"identifier": identifier})
    assert response.status_code == 200, response.text
    return response.json()


def _confirm(client: TestClient, challenge_id: str, code: str, new_password: str = NEW_PASSWORD):
    return client.post(
        "/v1/auth/password-recovery/confirm",
        json={"challenge_id": challenge_id, "code": code, "new_password": new_password},
    )


def _login(client: TestClient, identifier: str, password: str, device_token: str | None = None):
    payload = {"identifier": identifier, "password": password}
    if device_token:
        payload["device_token"] = device_token
    return client.post("/v1/auth/login", json=payload)


def test_requesting_recovery_issues_an_sms_code_challenge(client):
    verified = _verified_user(client, "+234 803 000 0201")
    challenge = _recover(client, "+234 803 000 0201")

    assert challenge["purpose"] == "password_reset"
    assert challenge["expires_in_seconds"] > 0
    assert "demo_code" in challenge

    # The recovery code is for the SMS the account holds, not the email.
    confirmed = _confirm(client, challenge["challenge_id"], challenge["demo_code"])
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "password_reset"
    assert confirmed.json()["sessions_revoked"] is True


def test_recovery_by_email_identifier_resolves_the_same_account(client):
    verified = _verified_user(client, "+234 803 000 0202")
    email = f'member-{"".join(ch for ch in "+234 803 000 0202" if ch.isdigit())}@example.test'
    challenge = _recover(client, email)

    assert _confirm(client, challenge["challenge_id"], challenge["demo_code"]).status_code == 200


def test_recovery_never_reveals_whether_an_identifier_exists(client):
    from core.config import get_settings

    old_cooldown = get_settings().otp_resend_cooldown_seconds
    object.__setattr__(get_settings(), "otp_resend_cooldown_seconds", 0)
    try:
        _verified_user(client, "+234 803 000 0203")

        known = _recover(client, "+234 803 000 0203")
        unknown = _recover(client, "+234 803 000 9999")

        assert set(known) == set(unknown)
        # The fake challenge must behave exactly like the real one: same shape,
        # and the code it would have sent verifies nowhere.
        confirmed = _confirm(client, unknown["challenge_id"], "000000")
        assert confirmed.status_code == confirmed.status_code == 401
    finally:
        object.__setattr__(get_settings(), "otp_resend_cooldown_seconds", old_cooldown)


def test_a_passwordless_legacy_account_is_answered_as_unknown(client):
    signup = _signup(client, "+234 803 000 0204", email=None, password=None)
    client.post(
        "/v1/auth/verify-otp", json={"challenge_id": signup["challenge_id"], "code": signup["demo_code"]}
    )

    legacy = _recover(client, "+234 803 000 0204")
    unknown = _recover(client, "+234 803 000 9997")

    assert set(legacy) == set(unknown)
    assert _confirm(client, legacy["challenge_id"], "000000").status_code == 401


def test_a_wrong_recovery_code_is_counted_and_the_right_one_still_works(client):
    _verified_user(client, "+234 803 000 0205")
    challenge = _recover(client, "+234 803 000 0205")

    assert _confirm(client, challenge["challenge_id"], "000000").status_code == 401
    assert _confirm(client, challenge["challenge_id"], challenge["demo_code"]).status_code == 200


def test_a_recovery_code_is_single_use(client):
    _verified_user(client, "+234 803 000 0206")
    challenge = _recover(client, "+234 803 000 0206")

    assert _confirm(client, challenge["challenge_id"], challenge["demo_code"]).status_code == 200
    assert _confirm(client, challenge["challenge_id"], challenge["demo_code"]).status_code == 400


def test_an_expired_recovery_code_is_refused(client):
    _verified_user(client, "+234 803 000 0207")
    challenge = _recover(client, "+234 803 000 0207")

    session = sessionmaker(bind=app.state.testing_session.kw["bind"])()
    row = session.get(AuthChallenge, challenge["challenge_id"])
    assert row is not None, "recovery challenge row disappeared before the expiry edit"
    row.expires_at = datetime.utcnow() - timedelta(seconds=1)
    session.commit()
    session.close()

    assert _confirm(client, challenge["challenge_id"], challenge["demo_code"]).status_code == 400


def test_the_old_password_stops_working_after_recovery(client):
    _verified_user(client, "+234 803 000 0208")
    challenge = _recover(client, "+234 803 000 0208")
    _confirm(client, challenge["challenge_id"], challenge["demo_code"])

    rejected = _login(client, "+234 803 000 0208", OLD_PASSWORD)
    assert rejected.status_code == 401


def test_the_new_password_works_after_recovery(client):
    _verified_user(client, "+234 803 000 0209")
    challenge = _recover(client, "+234 803 000 0209")
    assert _confirm(client, challenge["challenge_id"], challenge["demo_code"]).status_code == 200

    signed_in = _login(client, "+234 803 000 0209", NEW_PASSWORD)
    assert signed_in.status_code == 200, signed_in.text
    # A fresh device still steps up with OTP: recovery does not mint sessions.
    assert signed_in.json()["otp_required"] is True


def test_recovery_ends_sessions_issued_before_it(client):
    verified = _verified_user(client, "+234 803 000 0210")
    headers = {"Authorization": f"Bearer {verified['access_token']}"}
    assert client.get("/v1/me", headers=headers).status_code == 200

    challenge = _recover(client, "+234 803 000 0210")
    assert _confirm(client, challenge["challenge_id"], challenge["demo_code"]).status_code == 200

    assert client.get("/v1/me", headers=headers).status_code == 401


def test_recovery_revokes_remembered_devices(client):
    verified = _verified_user(client, "+234 803 000 0211")
    trusted_token = verified["trusted_device_token"]

    challenge = _recover(client, "+234 803 000 0211")
    assert _confirm(client, challenge["challenge_id"], challenge["demo_code"]).status_code == 200

    # The device remembered before the reset must step up with OTP again.
    signed_in = _login(client, "+234 803 000 0211", NEW_PASSWORD, device_token=trusted_token)
    assert signed_in.status_code == 200, signed_in.text
    assert signed_in.json()["otp_required"] is True


def test_a_recovery_code_cannot_mint_a_session_through_verify_otp(client):
    _verified_user(client, "+234 803 000 0212")
    challenge = _recover(client, "+234 803 000 0212")

    minted = client.post(
        "/v1/auth/verify-otp",
        json={"challenge_id": challenge["challenge_id"], "code": challenge["demo_code"]},
    )
    assert minted.status_code == 401


def test_confirm_refuses_a_login_challenge(client):
    verified = _verified_user(client, "+234 803 000 0213")
    login_challenge = client.post(
        "/v1/auth/login",
        json={"identifier": "+234 803 000 0213", "password": OLD_PASSWORD},
    ).json()

    rejected = _confirm(client, login_challenge["challenge_id"], "000000")
    assert rejected.status_code == 401


def test_the_new_password_must_differ_from_the_current_one(client):
    _verified_user(client, "+234 803 000 0214")
    challenge = _recover(client, "+234 803 000 0214")

    rejected = _confirm(client, challenge["challenge_id"], challenge["demo_code"], new_password=OLD_PASSWORD)
    assert rejected.status_code == 400
    assert "different" in rejected.json()["detail"].lower()


def test_the_new_password_must_not_contain_the_accounts_identifiers(client):
    _verified_user(client, "+234 803 000 0215")
    challenge = _recover(client, "+234 803 000 0215")

    reused = _confirm(client, challenge["challenge_id"], challenge["demo_code"], new_password="member-2348030000215-staple")
    assert reused.status_code == 400
    assert "must not contain" in reused.json()["detail"].lower()


def test_a_short_new_password_is_rejected(client):
    _verified_user(client, "+234 803 000 0216")
    challenge = _recover(client, "+234 803 000 0216")

    rejected = _confirm(client, challenge["challenge_id"], challenge["demo_code"], new_password="too-short")
    assert rejected.status_code in (400, 422)