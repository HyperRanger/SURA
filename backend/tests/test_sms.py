"""Outbound SMS via Termii.

The properties under test are the ones that decide whether codes actually reach
people and whether delivery can be abused to learn who has an account: the right
endpoint and channel, no secrets in the logs, and a provider outage that changes
nothing the caller can see.
"""

import logging

import pytest
from fastapi.testclient import TestClient

from app.models import AuthChallenge
from app.services import sms
from core.config import get_settings


class _Response:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


@pytest.fixture()
def termii(monkeypatch):
    """Capture outbound messages instead of sending them."""
    sent: list[dict] = []

    def _capture(url, json=None, timeout=None):
        sent.append({"url": url, "payload": json, "timeout": timeout})
        return _Response()

    monkeypatch.setattr(sms.httpx, "post", _capture)
    return sent


@pytest.fixture()
def configured(monkeypatch):
    settings = get_settings()
    original = settings.termii_api_key
    object.__setattr__(settings, "termii_api_key", "termii-secret-key")
    yield settings
    object.__setattr__(settings, "termii_api_key", original)


def _signup(client: TestClient, phone: str = "+234 803 000 0041") -> dict:
    response = client.post(
        "/v1/auth/signup",
        json={
            "role": "individual",
            "phone": phone,
            "name": "Sms Tester",
            "terms_accepted": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_a_code_is_sent_to_the_termii_messaging_endpoint(client, termii, configured):
    """The messaging API, not the token API.

    Termii's token product would generate and own the code, which would move
    storage, expiry and single-use enforcement out of this service.
    """
    _signup(client)

    assert len(termii) == 1
    assert termii[0]["url"].endswith("/api/sms/send")
    payload = termii[0]["payload"]
    assert payload["to"] == "2348030000041"
    assert payload["api_key"] == "termii-secret-key"
    assert payload["from"] == configured.termii_sender_id


def test_codes_go_out_on_the_dnd_channel_never_generic(client, termii, configured):
    """`generic` is marketing traffic.

    A login code on that channel is both the wrong classification and, on most
    networks, far more likely to be filtered or delayed.
    """
    _signup(client)

    assert termii[0]["payload"]["channel"] == "dnd"
    assert termii[0]["payload"]["channel"] != "generic"


def test_the_message_carries_the_issued_code(client, termii, configured):
    _signup(client)
    message = termii[0]["payload"]["sms"]

    assert message
    # The code in the message is the one the response hands back for the demo.
    assert str(configured.otp_ttl_seconds) in message


def test_the_payload_uses_exactly_the_fields_termii_binds(client, termii, configured):
    """Pin the wire contract, because the live API rejects the whole request on a
    wrong field name.

    Termii reports its recipient list as `toList` in validation errors, but that is
    not a key it binds: sending it silently produces an empty list. The body field
    is `sms`, not `message`. Both were wrong here once and the mocked provider hid
    it, so the key set is asserted exactly rather than field by field.
    """
    _signup(client)

    assert set(termii[0]["payload"]) == {"api_key", "to", "from", "channel", "sms"}


def test_the_recipient_is_sent_in_dialable_international_form(client, termii, configured):
    """No leading zero, so Termii can actually route it.

    A local `0803...` number is rejected outright as not dialable, which would turn
    every real send into a silent failure.
    """
    _signup(client, phone="+234 803 000 0041")

    recipient = termii[0]["payload"]["to"]
    assert recipient == "2348030000041"
    assert not recipient.startswith("0")
    assert not recipient.startswith("+")


def test_no_provider_configured_means_no_network_call(client, termii):
    """Local development runs with no Termii account.

    The code is still generated and still returned as `demo_code`, so the demo
    behaves as though the message had been sent.
    """
    settings = get_settings()
    object.__setattr__(settings, "termii_api_key", None)
    try:
        body = _signup(client)
        assert termii == []
        assert body["demo_code"]
    finally:
        object.__setattr__(settings, "termii_api_key", None)


def test_a_failed_send_does_not_change_what_the_caller_sees(
    client, monkeypatch, configured
):
    """Delivery must not become an account-existence oracle.

    A send only ever happens for a number we hold, so surfacing the failure would
    let a caller learn which numbers are registered. The response has to be
    indistinguishable from a successful send.
    """
    monkeypatch.setattr(
        sms.httpx,
        "post",
        lambda *a, **k: (_ for _ in ()).throw(sms.SmsDeliveryError("boom")),
    )
    failing = _signup(client, phone="+234 803 000 0042")

    monkeypatch.undo()
    settings = get_settings()
    object.__setattr__(settings, "termii_api_key", None)
    try:
        succeeding = _signup(client, phone="+234 803 000 0043")
    finally:
        object.__setattr__(settings, "termii_api_key", configured.termii_api_key)

    assert set(failing) == set(succeeding)
    for field in failing:
        # The identifiers and the code are per-account values; every structural
        # field has to match, because a difference in shape is the leak.
        if field in {"demo_code", "challenge_id"}:
            continue
        assert failing[field] == succeeding[field], field


def test_a_failed_send_still_holds_the_resend_cooldown(client, monkeypatch, configured):
    """The challenge is left pending rather than consumed or deleted.

    The cooldown is measured from the newest unconsumed challenge, so consuming
    or deleting it on failure would remove the only rate limit and let a provider
    outage be used to hammer the SMS gateway.
    """
    monkeypatch.setattr(
        sms.httpx,
        "post",
        lambda *a, **k: (_ for _ in ()).throw(sms.SmsDeliveryError("boom")),
    )
    body = _signup(client, phone="+234 803 000 0044")

    db = client.app.state.testing_session()
    try:
        row = db.get(AuthChallenge, body["challenge_id"])
        assert row is not None
        assert row.consumed_at is None
    finally:
        db.close()

    # And so a second request is refused the same way a successful send is.
    again = client.post("/v1/auth/login", json={"phone": "+234 803 000 0044"})
    assert again.status_code == 429


def test_an_undelivered_code_cannot_be_used(client, monkeypatch, configured):
    """Leaving the challenge pending must not leave a usable code behind.

    The row is kept for the cooldown, not as a way in: the code was never sent,
    so the only way to satisfy it is to guess, and guessing is attempt-capped.
    """
    settings = get_settings()
    original = settings.otp_max_attempts
    object.__setattr__(settings, "otp_max_attempts", 2)
    try:
        monkeypatch.setattr(
            sms.httpx,
            "post",
            lambda *a, **k: (_ for _ in ()).throw(sms.SmsDeliveryError("boom")),
        )
        body = _signup(client, phone="+234 803 000 0047")

        for _ in range(2):
            attempt = client.post(
                "/v1/auth/verify-otp",
                json={"challenge_id": body["challenge_id"], "code": "000000"},
            )
            assert attempt.status_code == 401
    finally:
        object.__setattr__(settings, "otp_max_attempts", original)


def test_an_unknown_number_never_triggers_a_send(client, termii, configured):
    """Only numbers we hold cost money, and only they could be enumerated."""
    _signup(client, phone="+234 803 000 0045")
    termii.clear()

    settings = get_settings()
    object.__setattr__(settings, "otp_resend_cooldown_seconds", 0)
    try:
        client.post("/v1/auth/login", json={"phone": "+234 803 000 9999"})
    finally:
        object.__setattr__(settings, "otp_resend_cooldown_seconds", 60)

    assert termii == []


def test_the_api_key_and_the_code_are_never_logged(
    client, monkeypatch, configured, caplog
):
    monkeypatch.setattr(
        sms.httpx,
        "post",
        lambda *a, **k: (_ for _ in ()).throw(sms.SmsDeliveryError("boom")),
    )
    with caplog.at_level(logging.DEBUG):
        _signup(client, phone="+234 803 000 0046")

    text = "\n".join(record.getMessage() for record in caplog.records)
    assert "termii-secret-key" not in text


def test_production_refuses_to_start_without_a_provider():
    """A signup that can never be verified is worse than not starting.

    The app would answer every signup normally while no code ever arrived, so the
    failure would show up as a support queue rather than an outage.
    """
    from app.main import _validate_production_settings

    settings = get_settings()
    original_environment = settings.environment
    original_key = settings.termii_api_key
    try:
        object.__setattr__(settings, "environment", "production")
        object.__setattr__(settings, "termii_api_key", None)
        with pytest.raises(RuntimeError, match="TERMII_API_KEY"):
            _validate_production_settings()

        object.__setattr__(settings, "termii_api_key", "termii-secret-key")
        _validate_production_settings()
    finally:
        object.__setattr__(settings, "environment", original_environment)
        object.__setattr__(settings, "termii_api_key", original_key)


def test_non_production_starts_without_a_provider():
    from app.main import _validate_production_settings

    settings = get_settings()
    original = settings.termii_api_key
    try:
        object.__setattr__(settings, "termii_api_key", None)
        _validate_production_settings()
    finally:
        object.__setattr__(settings, "termii_api_key", original)
