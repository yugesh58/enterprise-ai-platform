
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_liveness_returns_200():
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_returns_200_when_all_dependencies_are_healthy():
    with (
        patch("app.api.routes.health._check_sql_database"),
        patch("app.api.routes.health._check_document_database"),
        patch("app.api.routes.health._check_redis"),
        patch("app.api.routes.health._check_qdrant"),
    ):
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "dependencies": {
            "sql_database": "ok",
            "document_database": "ok",
            "redis": "ok",
            "qdrant": "ok",
        },
    }


def test_readiness_returns_503_when_a_dependency_fails():
    with (
        patch("app.api.routes.health._check_sql_database"),
        patch("app.api.routes.health._check_document_database"),
        patch(
            "app.api.routes.health._check_redis",
            side_effect=RuntimeError("Redis unavailable"),
        ),
        patch("app.api.routes.health._check_qdrant"),
    ):
        response = client.get("/health/ready")

    assert response.status_code == 503

    body = response.json()
    assert body["status"] == "not_ready"
    assert body["dependencies"]["redis"] == "error"
    assert body["dependencies"]["sql_database"] == "ok"
