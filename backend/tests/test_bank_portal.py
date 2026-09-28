from datetime import datetime

from app.bank.models import BankPartner, RiskFlag
from app.models import Redemption, User


def _bank_headers(auth_headers, bank_id="bank_demo"):
    return auth_headers("bank_admin_1", role="bank_admin", bank_id=bank_id)


def _seed_bank_data(client):
    db = client.app.state.testing_session()
    try:
        db.add_all([
            BankPartner(id="bank_demo", name="Demo Bank"),
            BankPartner(id="bank_other", name="Other Bank"),
            User(id="bank_amara", name="Amara Okafor", phone="amara@bank.test", bank_customer_id="CUST-0008241", bank_id="bank_demo", verified_at=datetime.utcnow()),
            User(id="bank_tunde", name="Tunde Adeyemi", phone="tunde@bank.test", bank_customer_id="CUST-0008242", bank_id="bank_demo"),
            User(id="other_customer", name="Private Customer", phone="private@bank.test", bank_customer_id="CUST-0009999", bank_id="bank_other"),
            RiskFlag(id="flag_amara", bank_id="bank_demo", user_id="bank_amara", rule="voucher_velocity", severity="medium", evidence_json='{"attempts": 3}'),
        ])
        db.commit()
    finally:
        db.close()


def test_bank_search_profile_and_customer_isolation(client, auth_headers):
    _seed_bank_data(client)
    headers = _bank_headers(auth_headers)

    search = client.get("/v1/bank/users?q=Amara", headers=headers)
    assert search.status_code == 200
    assert [user["user_id"] for user in search.json()] == ["bank_amara"]
    assert search.json()[0]["bank_customer_id"].endswith("8241")
    assert search.json()[0]["bank_customer_id"] != "CUST-0008241"

    profile = client.get("/v1/bank/users/bank_amara", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["score"] == 120
    assert profile.json()["score_report"]["score_version"] == "trd-5.2-v1"

    assert client.get("/v1/bank/users/other_customer", headers=headers).status_code == 404
    audit = client.get("/v1/bank/audit-log", headers=headers)
    assert audit.status_code == 200
    assert any(event["event_type"] == "customer_profile_viewed" for event in audit.json())


def test_bank_flags_require_bank_scope_and_support_resolution(client, auth_headers):
    _seed_bank_data(client)
    headers = _bank_headers(auth_headers)
    flags = client.get("/v1/bank/flags", headers=headers)
    assert flags.status_code == 200
    assert flags.json()[0]["flag_id"] == "flag_amara"

    resolved = client.post(
        "/v1/bank/flags/flag_amara/resolve",
        json={"action": "confirmed", "note": "Reviewed by risk analyst."},
        headers=headers,
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "confirmed"

    other_headers = _bank_headers(auth_headers, "bank_other")
    assert client.get("/v1/bank/flags", headers=other_headers).json() == []
    assert client.post(
        "/v1/bank/flags/flag_amara/resolve",
        json={"action": "dismissed", "note": "Should not access another bank."},
        headers=other_headers,
    ).status_code == 404


def test_bank_routes_reject_member_tokens(client, auth_headers):
    assert client.get("/v1/bank/overview", headers=auth_headers("member")).status_code == 403
