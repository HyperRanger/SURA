import hashlib
import hmac
import secrets
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


def create_token(subject: str, claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    payload: dict[str, Any] = {SESSION_CLAIM: SESSION_CLAIM_VALUE}
    payload.update(claims or {})
    payload["sub"] = subject
    payload.setdefault("iat", datetime.now(timezone.utc))
    payload.setdefault("exp", datetime.now(timezone.utc) + timedelta(seconds=settings.access_token_ttl_seconds))
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def is_local_session(claims: dict) -> bool:
    return claims.get(SESSION_CLAIM) == SESSION_CLAIM_VALUE


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
