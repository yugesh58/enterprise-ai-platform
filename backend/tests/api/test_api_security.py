from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from app.api.dependencies.security import require_api_key
from app.core.config import settings


test_app = FastAPI()
test_app.get(
    "/protected",
    dependencies=[Depends(require_api_key)],
)(lambda: {"status": "ok"})

client = TestClient(test_app)


def test_missing_api_key_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "API_AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "API_KEY", "test-secret")

    response = client.get("/protected")

    assert response.status_code == 401


def test_invalid_api_key_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "API_AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "API_KEY", "test-secret")

    response = client.get(
        "/protected",
        headers={"X-API-Key": "wrong-secret"},
    )

    assert response.status_code == 401


def test_valid_api_key_is_accepted(monkeypatch):
    monkeypatch.setattr(settings, "API_AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "API_KEY", "test-secret")

    response = client.get(
        "/protected",
        headers={"X-API-Key": "test-secret"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_missing_server_api_key_fails_closed(monkeypatch):
    monkeypatch.setattr(settings, "API_AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "API_KEY", "")

    response = client.get(
        "/protected",
        headers={"X-API-Key": "some-client-key"},
    )

    assert response.status_code == 503


def test_authentication_can_be_disabled_explicitly(monkeypatch):
    monkeypatch.setattr(settings, "API_AUTH_ENABLED", False)
    monkeypatch.setattr(settings, "API_KEY", "")

    response = client.get("/protected")

    assert response.status_code == 200