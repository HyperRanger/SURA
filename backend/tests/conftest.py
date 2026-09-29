import os
from pathlib import Path
import logging
import sys

from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


BACKEND_DIR = Path(__file__).resolve().parents[1]
backend_path = str(BACKEND_DIR)

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Forced, not defaulted. `setdefault` let an ambient DATABASE_URL/SECRET_KEY or a
# developer's .env change what the suite ran against, which made
# test_auth.py::test_demo_token_issues_a_token_for_the_online_demo fail with a 401
# for anyone whose DEMO_OTP_CODE was not 123456. The client fixture below already
# pins the database to in-memory SQLite, so pinning the rest keeps the suite
# hermetic and its results reproducible on any machine.
TEST_ENV = {
    "DATABASE_URL": "sqlite+pysqlite://",
    "SECRET_KEY": "test-secret-key",
    "JWT_ALGORITHM": "HS256",
    "DEMO_OTP_CODE": "123456",
    "ENVIRONMENT": "test",
}
for _key, _value in TEST_ENV.items():
    os.environ[_key] = _value

from app.database import Base, get_db
from app.main import app
from core.config import get_settings

# Settings are lru_cached, so the forced values above have to be picked up after
# anything that may already have built a Settings instance.
get_settings.cache_clear()


def pytest_configure() -> None:
    log_path = Path(__file__).resolve().parent / "pytest.log"
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    for handler in root_logger.handlers:
        if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == log_path:
            return

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root_logger.addHandler(file_handler)


@pytest.fixture()
def client() -> TestClient:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    app.state.testing_session = testing_session

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        del app.state.testing_session
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def auth_headers():
    settings = get_settings()

    def _headers(
        user_id: str,
        role: str | None = None,
        permissions: list[str] | None = None,
        institution_id: str | None = None,
    ) -> dict[str, str]:
        claims: dict[str, object] = {"sub": user_id}
        if role:
            claims["role"] = role
        if permissions:
            claims["permissions"] = permissions
        if institution_id:
            claims["institution_id"] = institution_id
        token = jwt.encode(claims, settings.secret_key, algorithm=settings.jwt_algorithm)
        return {"Authorization": "Bearer " + token}

    return _headers
