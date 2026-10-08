import pytest
from pydantic import ValidationError

from core.config import Settings


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_health_check_returns_503_when_database_is_unavailable(client, monkeypatch):
    monkeypatch.setattr("app.main._check_database", lambda db: False)
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "unavailable"}


def test_settings_require_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValidationError):
        # _env_file is a real pydantic-settings argument that disables .env
        # loading, and required fields are otherwise satisfied from the
        # environment. Neither is visible to a checker.
        Settings(_env_file=None)  # pyright: ignore[reportCallIssue, reportInvalidTypeForm]
