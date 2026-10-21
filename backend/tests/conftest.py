import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def configure_test_api_auth(monkeypatch):
    monkeypatch.setattr(settings, "API_AUTH_ENABLED", True)
    monkeypatch.setattr(
        settings,
        "API_KEY",
        "test-api-key-for-tests",
    )
