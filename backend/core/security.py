from typing import Any

import jwt

from core.config import get_settings


def create_token(subject: str, claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    payload = {"sub": subject, **(claims or {})}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
