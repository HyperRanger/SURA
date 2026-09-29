"""Outbound SMS.

Sura generates and verifies its own one-time codes and uses Termii only as the
pipe. That is deliberate: the alternative, Termii's own token product, would move
code generation, storage and verification to a third party and take the expiry,
attempt cap and single-use guarantees with it.

The provider is behind a tiny interface so the rest of the codebase never learns
which vendor is in use, and so tests can fail a send without a network call.
"""

import logging
from typing import Protocol

import httpx

from core.config import get_settings


logger = logging.getLogger(__name__)


class SmsDeliveryError(RuntimeError):
    """Raised when a message could not be handed to the provider.

    Callers must not let this reach the client as a distinct error. A send that
    fails only for real numbers would turn delivery into a way of discovering
    which phone numbers have accounts.
    """


class SmsProvider(Protocol):
    def send(self, to: str, message: str) -> None: ...


class NullSmsProvider:
    """Stand-in used when no provider is configured.

    Non-production only. Codes still reach the client through `demo_code` in the
    challenge response, so the demo behaves as if the message had been sent.
    """

    def send(self, to: str, message: str) -> None:
        logger.info("SMS not sent (no provider configured); message dropped.")


class TermiiSmsProvider:
    """Termii messaging API.

    Sends through `/api/sms/send` rather than the token endpoint, so the code is
    one this service generated and can revoke.
    """

    def __init__(self, api_key: str, base_url: str, sender_id: str, channel: str, timeout: int) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._sender_id = sender_id
        self._channel = channel
        self._timeout = timeout

    def send(self, to: str, message: str) -> None:
        payload = {
            "api_key": self._api_key,
            "to": to,
            "from": self._sender_id,
            "type": "plain",
            "channel": self._channel,
            "message": message,
        }
        try:
            response = httpx.post(
                f"{self._base_url}/api/sms/send",
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except Exception as exc:
            # The API key is never logged, and neither is the code inside the
            # message body.
            logger.error("SMS delivery failed: %s: %s", type(exc).__name__, exc)
            raise SmsDeliveryError("SMS delivery failed.") from exc


def get_sms_provider() -> SmsProvider:
    settings = get_settings()
    if not settings.is_sms_configured:
        return NullSmsProvider()
    return TermiiSmsProvider(
        api_key=settings.termii_api_key or "",
        base_url=settings.termii_base_url,
        sender_id=settings.termii_sender_id,
        channel=settings.termii_channel,
        timeout=settings.termii_timeout_seconds,
    )


def send_otp(to: str, code: str) -> None:
    """Send a one-time code, or raise SmsDeliveryError.

    A delivery failure is not a client error and must not be reported as one.
    """
    settings = get_settings()
    message = settings.otp_message_template.format(code=code, ttl_seconds=settings.otp_ttl_seconds)
    get_sms_provider().send(to=to, message=message)
