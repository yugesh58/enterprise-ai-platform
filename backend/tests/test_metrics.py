
from fastapi import FastAPI
from fastapi.testclient import TestClient
from prometheus_client import (
    CONTENT_TYPE_LATEST,
)

from app.api.middleware import RequestContextMiddleware
from app.api.routes.metrics import router as metrics_router
from app.core.config import settings
from app.core.metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
)


app = FastAPI()
app.add_middleware(RequestContextMiddleware)
app.include_router(metrics_router)


@app.get("/metrics-test/{item_id}")
def metrics_test_endpoint(item_id: int):
    return {"item_id": item_id}


client = TestClient(app)


def _metric_value(metric, **labels):
    return metric.labels(**labels)._value.get()


def test_metrics_endpoint_requires_api_key_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "API_AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "API_KEY", "test-metrics-key")

    response = client.get("/metrics")

    assert response.status_code == 401


def test_metrics_endpoint_returns_prometheus_format(monkeypatch):
    monkeypatch.setattr(settings, "API_AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "API_KEY", "test-metrics-key")

    response = client.get(
        "/metrics",
        headers={"X-API-Key": "test-metrics-key"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        CONTENT_TYPE_LATEST
    )
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text


def test_request_metrics_increment_for_route():
    route = "/metrics-test/{item_id}"
    method = "GET"

    before_count = _metric_value(
        HTTP_REQUESTS_TOTAL,
        method=method,
        route=route,
        status_code="200",
    )

    before_duration = HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method,
        route=route,
    )._sum.get()

    response = client.get("/metrics-test/123")

    assert response.status_code == 200
    assert _metric_value(
        HTTP_REQUESTS_TOTAL,
        method=method,
        route=route,
        status_code="200",
    ) == before_count + 1

    after_duration = HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method,
        route=route,
    )._sum.get()

    assert after_duration >= before_duration
