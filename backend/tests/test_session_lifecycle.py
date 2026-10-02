"""Session lifecycle, credential rotation and the platform audit trail.

Item 1 of the certification asks that a session end when the person says so, not
when its token happens to expire. Item 5 asks that a staff credential can be
rotated by its owner and by an administrator, with the old one provably dead.
Item 9 asks that the platform, not just one institution, be able to answer who
did what.

Each test below states the property being protected rather than the endpoint
shape, so a refactor that keeps the property passes.
"""

import json
import uuid

import pytest
from fastapi import HTTPException

from app.bank.contracts import BANK_STAFF_ROLE_PERMISSIONS
from app.bank.models import BankStaff
from app.models import PlatformAuditEvent, SessionRevocation, User
from app.services import audit, bank_auth_service
from app.services.demo_data import DEMO_BANK_ID, DEMO_BANK_PASSWORD, seed_demo_data
from core.passwords import hash_password
from core.security import create_token, verify_token

DEMO_ADMIN_EMAIL = "demo.admin@sura.local"
DEMO_RISK_EMAIL = "demo.risk@sura.local"


def _bank_session(client, email: str, password: str = DEMO_BANK_PASSWORD) -> dict[str, str]:
    """Sign in through the real path, second factor and all.

    Bank login is MFA-gated, so a token taken from the first response does not
    exist. Going through both steps means these tests exercise the same session
    an analyst actually gets.
    """
    login = client.post("/v1/bank/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    body = login.json()
    if "access_token" in body:
        return {"Authorization": f"Bearer {body['access_token']}"}

    verified = client.post(
        "/v1/bank/login/verify",
        json={"challenge_id": body["challenge_id"], "code": body["demo_code"]},
    )
    assert verified.status_code == 200, verified.text
    return {"Authorization": f"Bearer {verified.json()['access_token']}"}


def _db(client):
    session = client.app.state.testing_session()
    return session


def _seed(client):
    db = _db(client)
    try:
        seed_demo_data(db, reset=True)
        # The released demo seeds one full-permission portal account only. The
        # credential and least-privilege tests still need a second role, so they
        # construct it inside this isolated test database rather than making it
        # part of the public demo population.
        risk_user = User(
            id="usr_test_bank_risk",
            name="Test Bank Risk Analyst",
            phone="test.risk@sura.local",
            bank_id=DEMO_BANK_ID,
            role="bank_risk_analyst",
            verified_at=None,
        )
        db.add(risk_user)
        db.flush()
        db.add(BankStaff(
            id="stf_test_bank_risk",
            bank_id=DEMO_BANK_ID,
            user_id=risk_user.id,
            email=DEMO_RISK_EMAIL,
            password_hash=hash_password(DEMO_BANK_PASSWORD),
            role="bank_risk_analyst",
            permissions_json=json.dumps(sorted(BANK_STAFF_ROLE_PERMISSIONS["bank_risk_analyst"])),
            mfa_phone="2347065250899",
            status="active",
        ))
        db.commit()
    finally:
        db.close()


def _member_token(user_id: str) -> dict[str, str]:
    token = create_token(user_id, {"role": "individual"})
    return {"Authorization": f"Bearer {token}"}


def _bank_headers(auth_headers, user_id: str) -> dict[str, str]:
    return auth_headers(user_id, role="bank_admin", institution_id=DEMO_BANK_ID)


# --- item 1: signing out ends the session ---------------------------------


def test_logout_refuses_the_same_token_immediately(client):
    _seed(client)
    headers = _member_token("usr_demo_amara")

    assert client.get("/v1/me", headers=headers).status_code == 200

    signed_out = client.post("/v1/logout", headers=headers)
    assert signed_out.status_code == 200, signed_out.text

    after = client.get("/v1/me", headers=headers)
    assert after.status_code == 401
    assert "signed out" in after.json()["detail"].lower()


def test_logout_only_ends_the_session_it_was_given(client):
    _seed(client)
    first = _member_token("usr_demo_amara")
    second = _member_token("usr_demo_amara")

    assert client.post("/v1/logout", headers=first).status_code == 200

    # The whole point of per-token identifiers: one device signing out must not
    # sign the person out on their phone.
    assert client.get("/v1/me", headers=second).status_code == 200
    assert client.get("/v1/me", headers=first).status_code == 401


def test_logout_is_idempotent(client):
    _seed(client)
    headers = _member_token("usr_demo_amara")

    assert client.post("/v1/logout", headers=headers).status_code == 200
    repeat = client.post("/v1/logout", headers=headers)
    assert repeat.status_code == 200, repeat.text
    assert repeat.json()["revoked"] is False


def test_logout_requires_a_token(client):
    _seed(client)
    assert client.post("/v1/logout").status_code == 401


def test_logout_refuses_an_externally_issued_token(client, auth_headers):
    """Recording one locally would claim a revocation only the provider can make."""
    _seed(client)
    headers = auth_headers("external_user", role="bank_admin", institution_id=DEMO_BANK_ID)

    response = client.post("/v1/logout", headers=headers)
    assert response.status_code == 400
    assert "identity provider" in response.json()["detail"]


def test_logout_all_ends_every_session_including_untouched_ones(client):
    _seed(client)
    old_device = _member_token("usr_demo_amara")
    assert client.get("/v1/me", headers=old_device).status_code == 200

    assert client.post("/v1/logout-all", headers=old_device).status_code == 200

    # A token this person never signed out of, because it was minted on a device
    # they forgot about. It has to fail too.
    #
    # Issued at a whole second earlier rather than immediately, because ``iat``
    # has one-second resolution: a token minted in the same second as the
    # sign-out is genuinely undecidable and is treated as still valid.
    stale_device = {"Authorization": f"Bearer {create_token('usr_demo_amara', {'role': 'individual'}, backdate_seconds=5)}"}
    after = client.get("/v1/me", headers=stale_device)
    assert after.status_code == 401


def test_a_token_issued_after_logout_all_still_works(client):
    _seed(client)
    assert client.post("/v1/logout-all", headers=_member_token("usr_demo_amara")).status_code == 200

    fresh = _member_token("usr_demo_amara")
    assert client.get("/v1/me", headers=fresh).status_code == 200


def test_bank_staff_logout_ends_the_portal_session(client):
    _seed(client)
    # Signed in through the real path, so the token is one we minted and the
    # revocation has a row to write.
    headers = _bank_session(client, DEMO_ADMIN_EMAIL)

    assert client.get("/v1/bank/overview", headers=headers).status_code == 200
    assert client.post("/v1/bank/logout", headers=headers).status_code == 200

    after = client.get("/v1/bank/overview", headers=headers)
    assert after.status_code == 401


def test_revocation_row_carries_no_token_material(client):
    """A leaked audit row must not be replayable as a login."""
    _seed(client)
    headers = _member_token("usr_demo_amara")
    client.post("/v1/logout", headers=headers)

    db = _db(client)
    try:
        row = db.query(SessionRevocation).one()
        # The stored value is the token's identifier, never the token.
        assert not row.jti.startswith("ey")
        assert row.jti != headers["Authorization"]
        assert row.reason == "logout"
        assert row.expires_at is not None
    finally:
        db.close()


def test_expired_revocations_are_swept_on_the_next_logout(client):
    """Render runs no background worker, so a revocation set must not need one.

    The purge happens on the request path: the moment someone logs out, the rows
    that can no longer deny a real token are dropped. Without this, every logout
    would append a row that only stops being useful after the token's expiry, and
    the table would grow without bound on a deployment that has no cron.
    """
    from datetime import datetime, timedelta

    _seed(client)
    headers = _member_token("usr_demo_amara")
    assert client.post("/v1/logout", headers=headers).status_code == 200
    live_jti = verify_token(headers["Authorization"].split()[1])["jti"]

    db = _db(client)
    try:
        assert db.query(SessionRevocation).count() == 1

        expired_jti = "dead_" + uuid.uuid4().hex
        db.add(
            SessionRevocation(
                jti=expired_jti,
                user_id="usr_demo_amara",
                reason="logout",
                revoked_at=datetime.utcnow() - timedelta(days=31),
                expires_at=datetime.utcnow() - timedelta(days=1),
            )
        )
        db.commit()
        assert db.query(SessionRevocation).count() == 2
    finally:
        db.close()

    # The next logout sweeps rows whose token can no longer be presented.
    assert client.post("/v1/logout", headers=_member_token("usr_demo_amara")).status_code == 200

    db = _db(client)
    try:
        remaining = {row.jti for row in db.query(SessionRevocation).all()}
        assert expired_jti not in remaining
        assert live_jti in remaining
        # The sweep removed exactly the dead row; this logout adds its own.
        assert len(remaining) == 2
    finally:
        db.close()


# --- item 5: staff password change and reset ------------------------------


def _staff(session, user_id: str) -> BankStaff:
    return session.query(BankStaff).filter(BankStaff.user_id == user_id).one()


def test_staff_can_change_their_own_password_and_the_old_one_stops_working(client):
    _seed(client)
    db = _db(client)
    try:
        staff = _staff(db, "usr_demo_bank_admin")
        bank_auth_service.change_password(db, staff, DEMO_BANK_PASSWORD, "a-longer-passphrase-1")
    finally:
        db.close()

    old = client.post(
        "/v1/bank/login",
        json={"email": DEMO_ADMIN_EMAIL, "password": DEMO_BANK_PASSWORD},
    )
    assert old.status_code == 401

    # The new password gets a person all the way to a working session.
    assert _bank_session(client, DEMO_ADMIN_EMAIL, "a-longer-passphrase-1")


def test_password_change_requires_the_current_password(client):
    _seed(client)
    db = _db(client)
    try:
        staff = _staff(db, "usr_demo_bank_admin")
        with pytest.raises(HTTPException) as caught:
            bank_auth_service.change_password(db, staff, "not-the-password", "another-long-passphrase")
        # The generic message, so this endpoint cannot confirm which passwords
        # are close.
        assert caught.value.status_code == 401
    finally:
        db.close()


def test_password_change_refuses_the_same_password(client):
    _seed(client)
    db = _db(client)
    try:
        staff = _staff(db, "usr_demo_bank_admin")
        with pytest.raises(HTTPException) as caught:
            bank_auth_service.change_password(db, staff, DEMO_BANK_PASSWORD, DEMO_BANK_PASSWORD)
        assert caught.value.status_code == 400
    finally:
        db.close()


def test_password_change_refuses_one_containing_their_own_email(client):
    _seed(client)
    db = _db(client)
    try:
        staff = _staff(db, "usr_demo_bank_admin")
        with pytest.raises(HTTPException) as caught:
            bank_auth_service.change_password(
                db, staff, DEMO_BANK_PASSWORD, f"{DEMO_ADMIN_EMAIL}-plus-more"
            )
        assert "email" in caught.value.detail.lower()
    finally:
        db.close()


def test_changing_a_password_ends_every_session_the_person_held(client):
    _seed(client)
    session_headers = _bank_session(client, DEMO_ADMIN_EMAIL)
    assert client.get("/v1/bank/overview", headers=session_headers).status_code == 200

    changed = client.post(
        "/v1/bank/password",
        headers=session_headers,
        json={"current_password": DEMO_BANK_PASSWORD, "new_password": "a-longer-passphrase-1"},
    )
    assert changed.status_code == 200, changed.text

    after = client.get("/v1/bank/overview", headers=session_headers)
    assert after.status_code == 401


def test_admin_can_reset_a_colleagues_password(client):
    _seed(client)
    db = _db(client)
    try:
        actor = _staff(db, "usr_demo_bank_admin")
        target = _staff(db, "usr_test_bank_risk")
        bank_auth_service.reset_password(db, actor, target.id, "reset-passphrase-99")
    finally:
        db.close()

    assert _bank_session(client, DEMO_RISK_EMAIL, "reset-passphrase-99")


def test_a_non_admin_cannot_reset_anyone(client):
    _seed(client)
    db = _db(client)
    try:
        actor = _staff(db, "usr_test_bank_risk")
        target = _staff(db, "usr_demo_bank_admin")
        with pytest.raises(HTTPException) as caught:
            bank_auth_service.reset_password(db, actor, target.id, "reset-passphrase-99")
        assert caught.value.status_code == 403
    finally:
        db.close()


def test_admin_cannot_reset_their_own_password_through_the_reset_path(client):
    """Otherwise the reset endpoint would bypass proving the current password."""
    _seed(client)
    db = _db(client)
    try:
        actor = _staff(db, "usr_demo_bank_admin")
        with pytest.raises(HTTPException) as caught:
            bank_auth_service.reset_password(db, actor, actor.id, "reset-passphrase-99")
        assert caught.value.status_code == 400
    finally:
        db.close()


def test_admin_cannot_reset_a_staff_member_at_another_bank(client):
    _seed(client)
    db = _db(client)
    try:
        from app.bank.models import BankPartner

        other_bank = BankPartner(id="bnk_other", name="Other Bank")
        db.add(other_bank)
        db.flush()
        intruder = User(id="usr_other_staff", name="Outsider", phone="+2347000000001", role="bank_risk_analyst")
        db.add(intruder)
        db.flush()
        outside = BankStaff(
            id="stf_outside",
            bank_id="bnk_other",
            user_id="usr_other_staff",
            email="outsider@other.local",
            password_hash="x",
            role="bank_risk_analyst",
            permissions_json="[]",
            status="active",
        )
        db.add(outside)
        actor = _staff(db, "usr_demo_bank_admin")
        db.commit()

        with pytest.raises(HTTPException) as caught:
            bank_auth_service.reset_password(db, actor, outside.id, "reset-passphrase-99")
        assert caught.value.status_code == 404
    finally:
        db.close()


def test_permissions_cannot_exceed_the_role_map(client):
    """Otherwise a permission would be stored and only fail later at the route."""
    _seed(client)
    db = _db(client)
    try:
        actor = _staff(db, "usr_demo_bank_admin")
        target = _staff(db, "usr_test_bank_risk")
        with pytest.raises(HTTPException) as caught:
            bank_auth_service.change_permissions(db, actor, target.id, ["bank:settings:write"])
        assert caught.value.status_code == 400
        assert "bank_risk_analyst" in caught.value.detail
    finally:
        db.close()


def test_permissions_can_be_narrowed_and_take_effect_on_the_next_request(client):
    _seed(client)
    db = _db(client)
    try:
        actor = _staff(db, "usr_demo_bank_admin")
        target = _staff(db, "usr_test_bank_risk")
        bank_auth_service.change_permissions(db, actor, target.id, ["bank:overview:read"])
    finally:
        db.close()

    headers = _bank_session(client, DEMO_RISK_EMAIL)

    assert client.get("/v1/bank/overview", headers=headers).status_code == 200
    refused = client.get("/v1/bank/flags", headers=headers)
    assert refused.status_code == 403, refused.text


# --- item 9: platform audit -----------------------------------------------


def test_platform_audit_refuses_an_unregistered_event_type(client):
    """A typo must not create an event type nothing queries."""
    _seed(client)
    db = _db(client)
    try:
        with pytest.raises(ValueError):
            audit.record(db, event_type="not.a.real.event", subject_type="user", subject_id="usr_demo_amara")
    finally:
        db.close()


def test_successful_and_failed_bank_logins_are_both_recorded(client):
    _seed(client)

    # Cleared the password and the second factor, so this is a session.
    assert _bank_session(client, DEMO_ADMIN_EMAIL)

    bad = client.post(
        "/v1/bank/login",
        json={"email": DEMO_ADMIN_EMAIL, "password": "wrong"},
    )
    assert bad.status_code == 401

    db = _db(client)
    try:
        rows = db.query(PlatformAuditEvent).all()
        types = {row.event_type for row in rows}
        assert audit.LOGIN_SUCCEEDED in types
        assert audit.LOGIN_FAILED in types
        # The password was correct but the second factor never completed.
        assert audit.LOGIN_MFA_CHALLENGED in types

        # A trail that only records successes cannot answer "who tried".
        failure = next(row for row in rows if row.event_type == audit.LOGIN_FAILED)
        assert failure.subject_type == "bank_staff"
        assert failure.institution_id == DEMO_BANK_ID
    finally:
        db.close()


def test_password_change_is_recorded_at_platform_scope_without_the_secret(client):
    _seed(client)
    db = _db(client)
    try:
        staff = _staff(db, "usr_demo_bank_admin")
        bank_auth_service.change_password(db, staff, DEMO_BANK_PASSWORD, "a-longer-passphrase-1")
    finally:
        db.close()

    db = _db(client)
    try:
        event = (
            db.query(PlatformAuditEvent)
            .filter(PlatformAuditEvent.event_type == audit.PASSWORD_CHANGED)
            .one()
        )
        assert event.institution_id == DEMO_BANK_ID
        assert event.subject_type == "bank_staff"
        # Neither the old nor the new password may appear anywhere in the trail.
        serialised = json.dumps(
            [row.detail_json for row in db.query(PlatformAuditEvent).all()]
        )
        assert DEMO_BANK_PASSWORD not in serialised
        assert "a-longer-passphrase-1" not in serialised
    finally:
        db.close()


def test_platform_audit_rows_are_deleted_by_nothing_in_the_codebase():
    """Append-only by construction: the models are read and written, never removed."""
    import ast
    from pathlib import Path

    backend_dir = Path(__file__).resolve().parents[1]
    offenders = []
    for path in (backend_dir / "app").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = getattr(func, "attr", None)
            if name in {"delete", "drop"}:
                rendered = ast.dump(node)
                if "PlatformAuditEvent" in rendered:
                    offenders.append(f"{path.name}:{node.lineno}")

    assert not offenders, f"platform audit rows are deleted at: {offenders}"


def test_restriction_decision_is_recorded_at_platform_scope(client, auth_headers):
    _seed(client)
    headers = _bank_headers(auth_headers, "usr_demo_bank_admin")

    applied = client.post(
        "/v1/bank/users/usr_demo_amara/restriction",
        headers=headers,
        json={"action": "restricted", "reason": "Manual review under way."},
    )
    assert applied.status_code == 200, applied.text

    db = _db(client)
    try:
        event = (
            db.query(PlatformAuditEvent)
            .filter(PlatformAuditEvent.event_type == audit.ACCOUNT_RESTRICTED)
            .one()
        )
        assert event.subject_id == "usr_demo_amara"
        assert event.institution_id == DEMO_BANK_ID
        detail = json.loads(event.detail_json)
        assert detail["action"] == "restricted"
    finally:
        db.close()
