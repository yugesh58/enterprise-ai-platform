from fastapi.testclient import TestClient

from app.api.routes import health
from app.core.metrics import DEPENDENCY_HEALTH
from app.main import app


client = TestClient(app)


def test_readiness_updates_dependency_health_metrics(monkeypatch):
    monkeypatch.setattr(health, "_check_sql_database", lambda: None)
    monkeypatch.setattr(health, "_check_document_database", lambda: None)
    monkeypatch.setattr(health, "_check_redis", lambda: None)
    monkeypatch.setattr(health, "_check_qdrant", lambda: None)

    response = client.get("/health/ready")

    assert response.status_code == 200

    for dependency in (
        "sql_database",
        "document_database",
        "redis",
        "qdrant",
    ):
        assert (
            DEPENDENCY_HEALTH.labels(
                dependency=dependency
            )._value.get()
            == 1
        )


def test_readiness_records_unhealthy_dependency(monkeypatch):
    def fail():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(health, "_check_sql_database", fail)
    monkeypatch.setattr(health, "_check_document_database", lambda: None)
    monkeypatch.setattr(health, "_check_redis", lambda: None)
    monkeypatch.setattr(health, "_check_qdrant", lambda: None)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert (
        DEPENDENCY_HEALTH.labels(
            dependency="sql_database"
        )._value.get()
        == 0
    )