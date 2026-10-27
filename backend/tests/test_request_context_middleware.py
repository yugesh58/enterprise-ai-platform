
import logging
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.middleware import RequestContextMiddleware
from app.core.logging import get_logger
from app.core.request_context import request_id_var


app = FastAPI()
app.add_middleware(RequestContextMiddleware)

logger = get_logger("middleware-test")


@app.get("/test")
def test_endpoint():
    logger.info("Endpoint executed")
    return {"request_id": request_id_var.get()}


@app.get("/test-stream")
def test_stream():
    logger.info("Stream endpoint executed")
    return {"message": "stream test"}

@app.get("/test-error")
def error_endpoint():
    raise RuntimeError("test failure")

client = TestClient(app)


def test_request_id_is_returned_and_valid():
    response = client.get("/test")

    assert response.status_code == 200
    request_id = response.headers["x-request-id"]
    UUID(request_id)
    assert response.json()["request_id"] == request_id


def test_each_request_gets_a_unique_id():
    first = client.get("/test")
    second = client.get("/test")

    assert first.headers["x-request-id"] != second.headers["x-request-id"]


def test_request_id_is_in_application_logs(caplog):
    with caplog.at_level(logging.INFO, logger="middleware-test"):
        response = client.get("/test")

    request_id = response.headers["x-request-id"]
    assert any(
        record.message == "Endpoint executed"
        and getattr(record, "request_id", None) == request_id
        for record in caplog.records
    )


def test_request_context_is_reset_after_request():
    client.get("/test")

    assert request_id_var.get() == "-"


def test_request_id_header_is_returned_for_streaming_response():
    response = client.get("/test-stream")

    assert response.status_code == 200
    UUID(response.headers["x-request-id"])

def test_valid_incoming_request_id_is_preserved():
    request_id = "trace-abc-123"

    response = client.get(
        "/test",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == request_id
    assert response.json()["request_id"] == request_id


def test_invalid_incoming_request_id_is_replaced():
    response = client.get(
        "/test",
        headers={"X-Request-ID": "invalid id with spaces"},
    )

    assert response.status_code == 200

    request_id = response.headers["x-request-id"]
    UUID(request_id)
    assert response.json()["request_id"] == request_id


def test_excessively_long_request_id_is_replaced():
    response = client.get(
        "/test",
        headers={"X-Request-ID": "a" * 129},
    )

    assert response.status_code == 200
    UUID(response.headers["x-request-id"])


def test_error_response_preserves_incoming_request_id():
    request_id = "trace-error-456"

    response = TestClient(
        app,
        raise_server_exceptions=False,
    ).get(
        "/test-error",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 500
    assert response.headers["x-request-id"] == request_id

    body = response.json()["error"]
    assert body["code"] == "INTERNAL_SERVER_ERROR"
    assert body["request_id"] == request_id
    assert "test failure" not in response.text