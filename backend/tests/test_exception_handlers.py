
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.exception_handlers import register_exception_handlers
from app.api.middleware import RequestContextMiddleware


app = FastAPI()
register_exception_handlers(app)
app.add_middleware(RequestContextMiddleware)


@app.get("/test-http-error")
def http_error_endpoint():
    raise HTTPException(status_code=404, detail="Resource not found")


@app.get("/test-validation")
def validation_endpoint(item_id: int):
    return {"item_id": item_id}


@app.get("/test-unexpected-error")
def unexpected_error_endpoint():
    raise RuntimeError("database password must never reach the client")


client = TestClient(app, raise_server_exceptions=False)


def test_http_exception_uses_standard_error_envelope():
    response = client.get("/test-http-error")

    assert response.status_code == 404
    assert response.headers.get("x-request-id")
    body = response.json()["error"]
    assert body["code"] == "HTTP_ERROR"
    assert body["message"] == "Resource not found"
    assert body["request_id"] == response.headers["x-request-id"]


def test_validation_error_uses_standard_error_envelope():
    response = client.get("/test-validation", params={"item_id": "abc"})

    assert response.status_code == 422
    assert response.headers.get("x-request-id")
    body = response.json()["error"]
    assert body["code"] == "VALIDATION_ERROR"
    assert body["message"] == "Request validation failed."
    assert body["request_id"] == response.headers["x-request-id"]


def test_unexpected_error_is_sanitized():
    response = client.get("/test-unexpected-error")

    assert response.status_code == 500
    assert response.headers.get("x-request-id")
    body = response.json()["error"]
    assert body["code"] == "INTERNAL_SERVER_ERROR"
    assert body["message"] == "An unexpected error occurred."
    assert body["request_id"] == response.headers["x-request-id"]
    assert "database password" not in response.text
