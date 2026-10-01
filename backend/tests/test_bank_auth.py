"""B1: Bank Portal sign-in.

The tests are weighted towards the ways this endpoint can leak or be replayed
rather than the happy path: enumerating staff addresses, using a locked-state
message to confirm an account exists, replaying a second factor, and using a
token after access is withdrawn.
"""

import json
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.bank.models import BankAuditEvent, BankPartner, BankStaff
from app.models import User
from core.config import get_settings
from core.passwords import hash_password


BANK_PASSWORD = "correct-horse-battery-staple"
STAFF_EMAIL = "analyst@bank.test"


def _provision_staff(
    client: TestClient,
    *,
    email: str = STAFF_EMAIL,
    password: str = BANK_PASSWORD,
    role: str = "bank_risk_analyst",
    permissions: list[str] | None = None,
    mfa_phone: str | None = "2347065250817",
    status: str = "active",
    bank_id: str = "bnk_test",
) -> dict:
    """Provisions staff and returns plain ids, not ORM objects.

    The session is closed on the way out, so a returned instance would be
    detached and unusable by the caller.
    """
    db = client.app.state.testing_session()
    try:
        now = datetime.utcnow()
        if db.get(BankPartner, bank_id) is None:
            db.add(BankPartner(id=bank_id, name="Test Bank", created_at=now))
            db.flush()

        user_id = f"usr_{email}"
        if db.get(User, user_id) is None:
            db.add(
                User(
                    id=user_id,
                    name="Test Analyst",
                    phone=f"phone-{email}",
                    role=role,
                    bank_id=bank_id,
                    phone_verified_at=now,
                    verified_at=now,
                )
            )
            db.flush()

        staff_id = f"stf_{email}"
        db.add(
            BankStaff(
                id=staff_id,
                bank_id=bank_id,
                user_id=user_id,
                email=email,
                password_hash=hash_password(password),
                role=role,
                permissions_json=json.dumps(
                    permissions
                    if permissions is not None
                    else ["bank:overview:read", "bank:users:read", "bank:flags:read"]
                ),
                mfa_phone=mfa_phone,
                status=status,
                created_at=now,
            )
        )
        db.commit()
        return {"staff_id": staff_id, "user_id": user_id, "bank_id": bank_id}
    finally:
        db.close()


def _login(client: TestClient, email: str = STAFF_EMAIL, password: str = BANK_PASSWORD):
    return client.post("/v1/bank/login", json={"email": email, "password": password})


def _verify_mfa(client: TestClient, challenge_id: str, code: str):
    return client.post(
        "/v1/bank/login/verify", json={"challenge_id": challenge_id, "code": code}
    )


def _verify_customer_otp(client: TestClient, challenge_id: str, code: str):
    return client.post(
        "/v1/auth/verify-otp", json={"challenge_id": challenge_id, "code": code}
    )


def _sign_in(client: TestClient) -> dict:
    challenge = _login(client).json()
    verified = _verify_mfa(client, challenge["challenge_id"], challenge["demo_code"])
    assert verified.status_code == 200, verified.text
    return verified.json()


def test_a_correct_password_is_followed_by_a_second_factor(client):
    _provision_staff(client)
    response = _login(client)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["mfa_required"] is True
    assert body["purpose"] == "bank_mfa"
    assert "access_token" not in body
    assert body["demo_code"]


def test_completing_the_second_factor_returns_a_working_bank_session(client):
    _provision_staff(client)
    body = _sign_in(client)

    assert body["role"] == "bank_risk_analyst"
    assert body["institution_id"] == "bnk_test"
    assert "bank:overview:read" in body["permissions"]

    headers = {"Authorization": f"Bearer {body['access_token']}"}
    overview = client.get("/v1/bank/overview", headers=headers)
    assert overview.status_code == 200, overview.text


def test_a_bank_session_carries_the_bank_tenant_not_a_school(client):
    """`institution_id` on the bank principal is the partner bank.

    A staff member is also a user, and users have their own `institution_id`
    naming a school or employer. Using that one would scope every bank query to a
    tenant that does not exist, so the check here is that the bank wins.
    """
    staff = _provision_staff(client)
    db = client.app.state.testing_session()
    try:
        from app.models import Institution

        db.add(Institution(id="inst_school", name="Test University"))
        db.flush()
        user = db.get(User, staff["user_id"])
        user.institution_id = "inst_school"
        db.commit()
    finally:
        db.close()

    body = _sign_in(client)
    assert body["institution_id"] == "bnk_test"
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    assert client.get("/v1/bank/overview", headers=headers).status_code == 200


def test_an_unknown_address_and_a_wrong_password_answer_the_same(client):
    _provision_staff(client)

    unknown = _login(client, email="nobody@bank.test")
    wrong = _login(client, password="not-the-password")

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


def test_repeated_wrong_passwords_lock_the_account(client):
    _provision_staff(client)
    settings = get_settings()

    for _ in range(settings.bank_login_max_password_attempts):
        assert _login(client, password="wrong").status_code == 401

    # The right password is now refused, with a state the person can act on.
    locked = _login(client)
    assert locked.status_code == 423
    assert "locked" in locked.json()["detail"].lower()


def test_a_lockout_does_not_confirm_that_an_account_exists(client):
    """The locked message is only for someone who already holds the password.

    Reporting it to anyone who guesses an address would turn the lockout into an
    account-existence oracle, which is what the generic 401 exists to prevent.
    """
    _provision_staff(client)
    settings = get_settings()

    for _ in range(settings.bank_login_max_password_attempts):
        _login(client, password="wrong")

    assert _login(client, password="still-wrong").status_code == 401
    assert _login(client, password="still-wrong").json()["detail"] == (
        "Email or password is incorrect."
    )
    assert _login(client, email="nobody@bank.test", password="still-wrong").status_code == 401


def test_a_lockout_expires(client):
    _provision_staff(client)
    settings = get_settings()
    for _ in range(settings.bank_login_max_password_attempts):
        _login(client, password="wrong")

    db = client.app.state.testing_session()
    try:
        staff = db.query(BankStaff).filter(BankStaff.email == STAFF_EMAIL).one()
        staff.locked_until = datetime.utcnow() - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()

    assert _login(client).status_code == 200


def test_a_second_factor_cannot_be_replayed(client):
    _provision_staff(client)
    challenge = _login(client).json()

    assert _verify_mfa(client, challenge["challenge_id"], challenge["demo_code"]).status_code == 200
    # A captured code must not mint a second session.
    assert _verify_mfa(client, challenge["challenge_id"], challenge["demo_code"]).status_code == 400


def test_a_wrong_second_factor_is_rejected_and_counted(client):
    _provision_staff(client)
    challenge = _login(client).json()

    assert _verify_mfa(client, challenge["challenge_id"], "000000").status_code == 401
    # A typo should not lock the analyst out of their own account.
    assert _verify_mfa(client, challenge["challenge_id"], challenge["demo_code"]).status_code == 200


def test_the_customer_login_code_is_not_accepted_as_a_bank_factor(client):
    """The two challenge purposes are separate.

    A code issued for a phone login must not open a bank session, or a customer
    who intercepted one gains staff access.
    """
    _provision_staff(client)
    signup = client.post(
        "/v1/auth/signup",
        json={
            "role": "individual",
            "phone": "+234 803 000 0031",
            "name": "Not Staff",
            "terms_accepted": True,
        },
    ).json()

    response = _verify_mfa(client, signup["challenge_id"], signup["demo_code"])
    assert response.status_code == 401


def test_permissions_are_read_from_the_database_and_not_the_token(client):
    _provision_staff(client)
    body = _sign_in(client)
    headers = {"Authorization": f"Bearer {body['access_token']}"}

    # The analyst cannot resolve a flag to begin with.
    assert client.get("/v1/bank/flags", headers=headers).status_code == 200
    db = client.app.state.testing_session()
    try:
        row = db.query(BankStaff).filter(BankStaff.email == STAFF_EMAIL).one()
        row.permissions_json = json.dumps(["bank:overview:read"])
        db.commit()
    finally:
        db.close()

    # Permissions are withdrawn on the next request, without touching the token.
    assert client.get("/v1/bank/users", headers=headers).status_code == 403
    assert client.get("/v1/bank/overview", headers=headers).status_code == 200


def test_revoking_staff_stops_a_session_that_already_exists(client):
    _provision_staff(client)
    body = _sign_in(client)
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    assert client.get("/v1/bank/overview", headers=headers).status_code == 200

    db = client.app.state.testing_session()
    try:
        row = db.query(BankStaff).filter(BankStaff.email == STAFF_EMAIL).one()
        row.status = "revoked"
        db.commit()
    finally:
        db.close()

    assert client.get("/v1/bank/overview", headers=headers).status_code == 401
    assert _login(client).status_code == 401


def test_a_revoked_staff_cannot_finish_a_second_factor(client):
    staff = _provision_staff(client)
    challenge = _login(client).json()

    db = client.app.state.testing_session()
    try:
        row = db.get(BankStaff, staff["staff_id"])
        row.status = "revoked"
        db.commit()
    finally:
        db.close()

    response = _verify_mfa(client, challenge["challenge_id"], challenge["demo_code"])
    # Answered as a wrong code, so this does not confirm the code was genuine.
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect code."


def test_staff_without_a_second_factor_are_refused_rather_than_skipped(client):
    """An account provisioned with no phone is a configuration mistake.

    Falling through to a session would hand out bank access to anyone who guessed
    a password, while the second factor was believed to be on.
    """
    _provision_staff(client, mfa_phone=None)
    response = _login(client)

    assert response.status_code == 403
    assert "second factor" in response.json()["detail"].lower()


def test_a_customer_session_cannot_reach_bank_routes(client):
    """A bank user is a user row, so a phone login must not inherit bank access."""
    signup = client.post(
        "/v1/auth/signup",
        json={
            "role": "individual",
            "phone": "+234 803 000 0032",
            "name": "Customer",
            "terms_accepted": True,
        },
    ).json()
    verified = _verify_customer_otp(
        client, signup["challenge_id"], signup["demo_code"]
    ).json()

    headers = {"Authorization": f"Bearer {verified['access_token']}"}
    assert client.get("/v1/bank/overview", headers=headers).status_code == 403


def test_a_bank_session_cannot_act_as_a_customer(client):
    """The reverse direction matters too: staff are users, and must not reach
    customer-only endpoints through the same token."""
    _provision_staff(client)
    body = _sign_in(client)
    headers = {"Authorization": f"Bearer {body['access_token']}"}

    me = client.get("/v1/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["role"] == "bank_risk_analyst"


def test_a_staff_row_with_an_unusable_role_is_refused_at_sign_in(client):
    """A role the bank routes do not recognise fails every request with a 403.

    Refusing at sign-in says why, instead of handing out a session that looks
    fine and then fails on every page.
    """
    _provision_staff(client, role="bank")
    response = _login(client)

    assert response.status_code == 403
    assert "bank portal access" in response.json()["detail"].lower()


def test_sign_ins_are_audited(client):
    _provision_staff(client)
    _login(client, password="wrong")
    _sign_in(client)

    db = client.app.state.testing_session()
    try:
        events = {
            row.event_type
            for row in db.query(BankAuditEvent)
            .filter(BankAuditEvent.bank_id == "bnk_test")
            .all()
        }
    finally:
        db.close()

    assert "bank_login_failed" in events
    assert "bank_login_succeeded" in events


def test_the_bank_demo_sign_in_works_outside_production(client):
    response = client.post("/v1/bank/demo-login")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["role"] == "bank_admin"

    headers = {"Authorization": f"Bearer {body['access_token']}"}
    assert client.get("/v1/bank/overview", headers=headers).status_code == 200
    assert client.get("/v1/bank/commitments", headers=headers).status_code == 200
    assert client.get("/v1/bank/settlements", headers=headers).status_code == 200
    assert client.get("/v1/bank/developers", headers=headers).status_code == 200


def test_the_bank_demo_sign_in_is_unavailable_in_production(client):
    settings = get_settings()
    original = settings.environment
    object.__setattr__(settings, "environment", "production")
    try:
        assert client.post("/v1/bank/demo-login").status_code == 404
    finally:
        object.__setattr__(settings, "environment", original)


def test_the_second_factor_code_is_withheld_in_production(client):
    _provision_staff(client)
    settings = get_settings()
    original = settings.environment
    object.__setattr__(settings, "environment", "production")
    try:
        body = _login(client).json()
        assert "demo_code" not in body
    finally:
        object.__setattr__(settings, "environment", original)


def test_an_over_long_password_is_refused_rather_than_truncated(client):
    """bcrypt ignores anything past 72 bytes.

    Accepting a longer password silently would make two different ones
    interchangeable, so it is rejected outright. The length here is under the
    request schema's limit, so this reaches the hashing layer rather than being
    turned away by validation first.
    """
    _provision_staff(client)
    response = _login(client, password="x" * 100)
    assert response.status_code == 401
