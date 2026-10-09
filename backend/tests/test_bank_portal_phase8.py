"""Phase 8 contract checks for the complete Bank Portal surface."""

from app.bank.models import BankPartner
from app.models import Commitment, CommitmentMember, Contribution, User
from app.services.demo_data import DEMO_BANK_ID, DEMO_COMMITMENT_ID, seed_demo_data


def _headers(auth_headers):
    return auth_headers("phase8_admin", role="bank_admin", institution_id=DEMO_BANK_ID)


def _seed(client):
    db = client.app.state.testing_session()
    try:
        seed_demo_data(db, reset=True)
        db.commit()
    finally:
        db.close()


def test_monitoring_filters_details_and_audit_export(client, auth_headers):
    _seed(client)
    headers = _headers(auth_headers)

    overview = client.get("/v1/bank/overview", headers=headers)
    assert overview.status_code == 200, overview.text
    assert overview.json()["customers"] == 90
    assert "recent_settlements" in overview.json()

    users = client.get("/v1/bank/users?verified=true&commitment_status=active", headers=headers)
    assert users.status_code == 200, users.text
    assert {"usr_demo_amara", "usr_demo_tunde"}.issubset({row["user_id"] for row in users.json()})

    commitments = client.get("/v1/bank/commitments?q=Laptop&status=active", headers=headers)
    assert commitments.status_code == 200, commitments.text
    assert commitments.json()[0]["commitment_id"] == DEMO_COMMITMENT_ID

    detail = client.get(f"/v1/bank/commitments/{DEMO_COMMITMENT_ID}", headers=headers)
    assert detail.status_code == 200, detail.text
    assert len(detail.json()["payout_schedule"]) == 2
    assert detail.json()["vendor"]["verified"] is True

    flag = client.get("/v1/bank/flags?status=open&severity=low", headers=headers)
    assert flag.status_code == 200, flag.text
    flag_id = flag.json()[0]["flag_id"]
    flag_detail = client.get(f"/v1/bank/flags/{flag_id}", headers=headers)
    assert flag_detail.status_code == 200, flag_detail.text

    filtered_audit = client.get("/v1/bank/audit-log?event_type=demo_data_seeded", headers=headers)
    assert filtered_audit.status_code == 200, filtered_audit.text
    assert len(filtered_audit.json()) == 1
    exported = client.post("/v1/bank/audit-log/export", headers=headers)
    assert exported.status_code == 200, exported.text
    assert "event_type" in exported.text

    settlement = client.get(f"/v1/bank/settlements?commitment_id={DEMO_COMMITMENT_ID}&status=settled", headers=headers)
    assert settlement.status_code == 200, settlement.text
    assert settlement.json()[0]["simulated"] is True


def test_developer_team_and_settings_endpoints(client, auth_headers):
    _seed(client)
    headers = _headers(auth_headers)

    developer_home = client.get("/v1/bank/developers", headers=headers)
    assert developer_home.status_code == 200, developer_home.text
    assert developer_home.json()["authentication"] == "X-Sura-API-Key"

    created = client.post(
        "/v1/bank/webhooks",
        headers=headers,
        json={"url": "https://demo-bank.example.test/sura", "events": ["score.updated"]},
    )
    assert created.status_code == 201, created.text
    deleted = client.delete(f"/v1/bank/webhooks/{created.json()['webhook_id']}", headers=headers)
    assert deleted.status_code == 204, deleted.text
    assert client.get("/v1/bank/webhooks", headers=headers).json()[0]["status"] == "disabled"

    staff = client.post(
        "/v1/bank/team",
        headers=headers,
        json={
            "name": "Portal Reviewer",
            "email": "reviewer@demo-bank.test",
            "role": "bank_risk_analyst",
            "mfa_phone": "2347065250999",
            "temporary_password": "temporary-password-123",
        },
    )
    assert staff.status_code == 201, staff.text
    changed = client.patch(f"/v1/bank/team/{staff.json()['staff_id']}", headers=headers, json={"status": "revoked"})
    assert changed.status_code == 200, changed.text
    assert changed.json()["status"] == "revoked"
    assert any(row["staff_id"] == staff.json()["staff_id"] for row in client.get("/v1/bank/team", headers=headers).json())

    settings = client.patch(
        "/v1/bank/settings",
        headers=headers,
        json={"environment": "sandbox", "supported_vendor_categories": ["education", "electronics"], "retention_days": 730, "security_settings": {"mfa_required": True}},
    )
    assert settings.status_code == 200, settings.text
    assert settings.json()["retention_days"] == 730
    assert settings.json()["security_settings"]["mfa_required"] is True

    db = client.app.state.testing_session()
    try:
        assert db.get(BankPartner, DEMO_BANK_ID).environment == "sandbox"
    finally:
        db.close()


def test_commitment_detail_does_not_disclose_another_bank_customer(client, auth_headers):
    _seed(client)
    db = client.app.state.testing_session()
    try:
        db.add(BankPartner(id="bank_outside", name="Outside Bank"))
        db.add(User(id="outside_customer", name="Outside Customer", phone="outside@bank.test", bank_id="bank_outside"))
        db.add(Commitment(
            id="cmt_cross_bank", creator_id="usr_demo_amara", type="rotating", title="Shared test group",
            vendor_id="vnd_demo_electronics", contribution_amount=100, frequency="weekly", cycles=1,
            status="active", invite_code="SURA-CROSS-BANK", payout_order_json='["usr_demo_amara", "outside_customer"]',
        ))
        db.add_all([
            CommitmentMember(commitment_id="cmt_cross_bank", user_id="usr_demo_amara", role="contributor"),
            CommitmentMember(commitment_id="cmt_cross_bank", user_id="outside_customer", role="contributor"),
            Contribution(id="ctr_cross_bank", commitment_id="cmt_cross_bank", cycle_number=1, user_id="outside_customer", amount=100, event_id="evt_cross_bank", status="full", rule_trace_json="{}"),
        ])
        db.commit()
    finally:
        db.close()

    response = client.get("/v1/bank/commitments/cmt_cross_bank", headers=_headers(auth_headers))
    assert response.status_code == 200, response.text
    body = response.json()
    assert [member["user_id"] for member in body["members"]] == ["usr_demo_amara"]
    assert body["contributions"] == []
