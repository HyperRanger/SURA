import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from core.config import get_settings

OTP_DIGITS = 6

# Marks a token this service minted. Sessions carrying it are re-checked against
# the database on every request, so a role change or a deleted account takes
# effect immediately instead of at token expiry. Tokens from an external
# provider, such as the bank portal's identity integration, do not carry it and
# are trusted on their claims per the documented provider contract.
SESSION_CLAIM = "sura_session"
SESSION_CLAIM_VALUE = "member"

# Millisecond-precision issue instant. See ``create_token``.
ISSUE_MS_CLAIM = "sura_iat_ms"


def create_token(
    subject: str,
    claims: dict[str, Any] | None = None,
    *,
    backdate_seconds: int = 0,
) -> str:
    """Mint a session token.

    ``backdate_seconds`` exists so a caller can produce a token that looks like
    it was issued earlier, which is how "sign out everywhere" is tested. Nothing
    in the request path uses it.
    """
    settings = get_settings()
    payload: dict[str, Any] = {SESSION_CLAIM: SESSION_CLAIM_VALUE}
    payload.update(claims or {})
    payload["sub"] = subject
    # A unique per-token identifier, so signing out can revoke this exact
    # session without affecting any other session the same person holds.
    payload.setdefault("jti", uuid.uuid4().hex)
    issued = datetime.now(timezone.utc) - timedelta(seconds=backdate_seconds)
    payload.setdefault("iat", issued)
    # ``iat`` is second-granular by spec, which cannot order a token against a
    # sign-out that happened in the same second. This carries the same instant at
    # millisecond precision so "sign out everywhere" has no ambiguity to fall
    # back on. Older tokens without it fall back to the seconds comparison.
    payload.setdefault(ISSUE_MS_CLAIM, int(issued.timestamp() * 1000))
    payload.setdefault("exp", issued + timedelta(seconds=settings.access_token_ttl_seconds))
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def is_local_session(claims: dict) -> bool:
    return claims.get(SESSION_CLAIM) == SESSION_CLAIM_VALUE


def token_expiry(claims: dict) -> datetime | None:
    """The token's expiry as a naive UTC datetime, matching how we store dates.

    SQLAlchemy columns here are naive UTC throughout, so converting to an aware
    value would mix both conventions in one column.
    """
    expiry = claims.get("exp")
    if expiry is None:
        return None
    return datetime.fromtimestamp(expiry, tz=timezone.utc).replace(tzinfo=None)


def token_issued_before(claims: dict, cutoff: datetime) -> bool | None:
    """Was this token issued before ``cutoff``? ``None`` if it cannot be told.

    Prefers the millisecond claim and falls back to second-granular ``iat``, so a
    token minted before this change still compares correctly, just at coarser
    resolution.
    """
    issued_ms = claims.get(ISSUE_MS_CLAIM)
    if issued_ms is not None:
        issued = datetime.fromtimestamp(issued_ms / 1000, tz=timezone.utc).replace(tzinfo=None)
        return issued < cutoff

    issued_at = claims.get("iat")
    if issued_at is None:
        return None
    issued = datetime.fromtimestamp(issued_at, tz=timezone.utc).replace(tzinfo=None)
    # Whole seconds only, so a token minted in the same second as the cut-off is
    # not wrongly treated as older than it.
    return issued < cutoff.replace(microsecond=0)


def verify_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


def generate_otp() -> str:
    """A six-digit code from a cryptographic source, not `random`."""
    return "".join(secrets.choice("0123456789") for _ in range(OTP_DIGITS))


def new_otp_salt() -> str:
    return secrets.token_hex(16)


def hash_otp(code: str, salt: str) -> str:
    """Salted SHA-256 of a one-time code.

    The code is short and single-use, so this only has to stop a leaked database
    row from being replayed as a login. It is not a substitute for a slow KDF and
    is not used for passwords.
    """
    return hashlib.sha256(f"{salt}:{code}".encode("utf-8")).hexdigest()


def otp_matches(code: str, salt: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_otp(code, salt), expected_hash)
