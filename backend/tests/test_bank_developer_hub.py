from datetime import datetime, timedelta, timezone

from app.bank.models import BankApiKey, BankPartner, WebhookSubscription
from app.models import User


def _headers(auth_headers, bank_id="bank_demo"):
    return auth_headers(
        "integration_engineer_1",
        role="bank_integration_engineer",
        permissions=["bank:developer:write"],
        institution_id=bank_id,
    )


def _seed_bank(client):
    db = client.app.state.testing_session()
    try:
        db.add_all([
            BankPartner(id="bank_demo", name="Demo Bank"),
            BankPartner(id="bank_other", name="Other Bank"),
            User(id="bank_customer", name="Bank Customer", phone="customer@bank.test", bank_id="bank_demo"),
            User(id="other_customer", name="Other Customer", phone="customer@other.test", bank_id="bank_other"),
        ])
        db.commit()
    finally:
        db.close()


def test_api_key_is_revealed_once_and_is_bank_scoped(client, auth_headers):
    _seed_bank(client)
    headers = _headers(auth_headers)
    created = client.post(
        "/v1/bank/api-keys",
        headers=headers,
        json={
            "name": "Demo integration",
            "scopes": ["score:read"],
            "environment": "sandbox",
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["secret"].startswith("sk_sura_")
    assert body["secret_revealed_once"] is True

    listed = client.get("/v1/bank/api-keys", headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["key_id"] == body["key_id"]
    assert "secret" not in listed.json()[0]
    assert "secret_hash" not in listed.json()[0]

    machine_headers = {"X-Sura-API-Key": body["secret"]}
    score = client.get("/v1/integrations/customers/bank_customer/score", headers=machine_headers)
    assert score.status_code == 200, score.text
    assert score.json()["user_id"] == "bank_customer"
    assert client.get("/v1/integrations/customers/other_customer/score", headers=machine_headers).status_code == 404
    assert client.get("/v1/integrations/customers/bank_customer/commitments", headers=machine_headers).status_code == 403

    db = client.app.state.testing_session()
    try:
        stored = db.get(BankApiKey, body["key_id"])
        assert stored.secret_hash != body["secret"]
    finally:
        db.close()

    other = client.post(f"/v1/bank/api-keys/{body['key_id']}/rotate", headers=_headers(auth_headers, "bank_other"))
    assert other.status_code == 404

    rotated = client.post(f"/v1/bank/api-keys/{body['key_id']}/rotate", headers=headers)
    assert rotated.status_code == 200, rotated.text
    assert rotated.json()["rotated_key_id"] == body["key_id"]
    assert rotated.json()["secret"] != body["secret"]
    assert client.get("/v1/integrations/customers/bank_customer/score", headers=machine_headers).status_code == 401


def test_webhook_is_signed_revealed_once_and_has_audit_delivery(client, auth_headers):
    _seed_bank(client)
    headers = _headers(auth_headers)
    created = client.post(
        "/v1/bank/webhooks",
        headers=headers,
        json={"url": "https://bank.example.test/sura/webhook", "events": ["contribution.recorded", "score.updated"]},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["signing_secret"].startswith("whsec_sura_")

    listed = client.get("/v1/bank/webhooks", headers=headers)
    assert listed.status_code == 200
    assert "signing_secret" not in listed.json()[0]

    db = client.app.state.testing_session()
    try:
        stored = db.get(WebhookSubscription, body["webhook_id"])
        assert stored.signing_secret_hash != body["signing_secret"]
        assert stored.signing_secret_encrypted != body["signing_secret"]
    finally:
        db.close()

    delivery = client.post(f"/v1/bank/webhooks/{body['webhook_id']}/test", headers=headers)
    assert delivery.status_code == 200, delivery.text
    assert delivery.json()["status"] == "simulated_success"
    assert delivery.json()["signature"].startswith("sha256=")
    assert delivery.json()["payload"]["type"] == "webhook.test"

    deliveries = client.get(f"/v1/bank/webhooks/{body['webhook_id']}/deliveries", headers=headers)
    assert deliveries.status_code == 200
    assert deliveries.json()[0]["delivery_id"] == delivery.json()["delivery_id"]

    rotated = client.post(f"/v1/bank/webhooks/{body['webhook_id']}/rotate-secret", headers=headers)
    assert rotated.status_code == 200
    assert rotated.json()["signing_secret"] != body["signing_secret"]


def test_webhook_contract_rejects_non_https_and_unauthorised_access(client, auth_headers):
    _seed_bank(client)
    headers = _headers(auth_headers)
    rejected = client.post(
        "/v1/bank/webhooks",
        headers=headers,
        json={"url": "http://bank.example.test/webhook", "events": ["score.updated"]},
    )
    assert rejected.status_code == 400

    member = client.get("/v1/bank/events", headers=auth_headers("member_1"))
    assert member.status_code == 403
    events = client.get("/v1/bank/events", headers=headers)
    assert events.status_code == 200
    assert {event["event_type"] for event in events.json()} >= {"contribution.recorded", "score.updated"}

    unsupported_scope = client.post(
        "/v1/bank/api-keys",
        headers=headers,
        json={"name": "Invalid scope", "scopes": ["admin:all"]},
    )
    assert unsupported_scope.status_code == 400
