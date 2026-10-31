from unittest.mock import MagicMock

import pytest
import redis
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.dependencies import rate_limit as limiter
from app.core.config import settings


TEST_API_KEY = "test-api-key-for-tests"


@pytest.fixture
def rate_limit_app(monkeypatch):
    monkeypatch.setattr(settings, "API_AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "API_KEY", TEST_API_KEY)
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "RATE_LIMIT_REQUESTS", 2)
    monkeypatch.setattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(
        settings,
        "RATE_LIMIT_KEY_SECRET",
        "test-hmac-secret",
    )

    app = FastAPI()

    @app.get("/limited", dependencies=[Depends(limiter.enforce_rate_limit)])
    def limited():
        return {"status": "ok"}

    return TestClient(app)


def mock_eval(allowed: int, retry_after: int = 0, count: int = 1):
    client = MagicMock()
    client.eval.return_value = [allowed, retry_after, count]
    return client


def test_request_is_allowed(rate_limit_app, monkeypatch):
    fake_redis = mock_eval(1, 0, 1)
    monkeypatch.setattr(limiter, "get_redis_client", lambda: fake_redis)

    response = rate_limit_app.get(
        "/limited",
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "2"
    assert response.headers["X-RateLimit-Remaining"] == "1"
    fake_redis.eval.assert_called_once()


def test_limit_exceeded_returns_429(rate_limit_app, monkeypatch):
    fake_redis = mock_eval(0, 17, 2)
    monkeypatch.setattr(limiter, "get_redis_client", lambda: fake_redis)

    response = rate_limit_app.get(
        "/limited",
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 429
    assert response.json()["detail"] == (
        "Rate limit exceeded. Please try again later."
    )
    assert response.headers["Retry-After"] == "17"
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert response.headers["X-RateLimit-Limit"] == "2"


def test_missing_api_key_returns_401(rate_limit_app, monkeypatch):
    fake_redis = mock_eval(1)
    monkeypatch.setattr(limiter, "get_redis_client", lambda: fake_redis)

    response = rate_limit_app.get("/limited")

    assert response.status_code == 401
    fake_redis.eval.assert_not_called()


def test_disabled_rate_limiting_skips_redis(
    rate_limit_app,
    monkeypatch,
):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)
    fake_redis = mock_eval(1)
    monkeypatch.setattr(limiter, "get_redis_client", lambda: fake_redis)

    response = rate_limit_app.get(
        "/limited",
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 200
    fake_redis.eval.assert_not_called()


def test_redis_failure_fails_closed(rate_limit_app, monkeypatch):
    fake_redis = MagicMock()
    fake_redis.eval.side_effect = redis.RedisError("connection failed")
    monkeypatch.setattr(limiter, "get_redis_client", lambda: fake_redis)

    response = rate_limit_app.get(
        "/limited",
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Rate limiting service is unavailable."
    )


def test_missing_hmac_secret_fails_closed(
    rate_limit_app,
    monkeypatch,
):
    monkeypatch.setattr(settings, "RATE_LIMIT_KEY_SECRET", "")
    fake_redis = mock_eval(1)
    monkeypatch.setattr(limiter, "get_redis_client", lambda: fake_redis)

    response = rate_limit_app.get(
        "/limited",
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 503
    fake_redis.eval.assert_not_called()
