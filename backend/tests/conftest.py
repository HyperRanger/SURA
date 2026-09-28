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

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("DEMO_OTP_CODE", "123456")

from app.database import Base, get_db
from app.main import app
from core.config import get_settings


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

    def _headers(user_id: str, role: str | None = None, permissions: list[str] | None = None) -> dict[str, str]:
        claims: dict[str, object] = {"sub": user_id}
        if role:
            claims["role"] = role
        if permissions:
            claims["permissions"] = permissions
        token = jwt.encode(claims, settings.secret_key, algorithm=settings.jwt_algorithm)
        return {"Authorization": "Bearer " + token}

    return _headers
