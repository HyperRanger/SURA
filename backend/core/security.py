import jwt

from core.config import get_settings


def create_token(subject: str) -> str:
    settings = get_settings()
    payload = {"sub": subject}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
