
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.exception_handlers import register_exception_handlers
from app.api.middleware import RequestContextMiddleware
from app.core.exceptions import (
    AgentExecutionError,
    ApplicationValidationError,
    EnterpriseAIError,
    RouterError,
    UnauthorizedError,
)

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

@app.get("/test-app-validation-error")
def app_validation_error_endpoint():
    raise ApplicationValidationError("Invalid document input")


@app.get("/test-unauthorized-error")
def unauthorized_error_endpoint():
    raise UnauthorizedError("Authentication failed")


@app.get("/test-agent-error")
def agent_error_endpoint():
    raise AgentExecutionError("Provider secret must not leak")


@app.get("/test-router-error")
def router_error_endpoint():
    raise RouterError("Routing details must not leak")


@app.get("/test-enterprise-error")
def enterprise_error_endpoint():
    raise EnterpriseAIError("Internal details must not leak")

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
import pytest


@pytest.mark.parametrize(
    ("path", "status_code", "error_code"),
    [
        (
            "/test-app-validation-error",
            422,
            "APPLICATION_VALIDATION_ERROR",
        ),
        ("/test-unauthorized-error", 401, "UNAUTHORIZED"),
        ("/test-agent-error", 502, "AGENT_EXECUTION_ERROR"),
        ("/test-router-error", 500, "ROUTER_ERROR"),
        ("/test-enterprise-error", 500, "APPLICATION_ERROR"),
    ],
)
def test_application_exceptions_use_standard_error_envelope(
    path,
    status_code,
    error_code,
):
    response = client.get(path)

    assert response.status_code == status_code
    assert response.headers.get("x-request-id")

    body = response.json()["error"]
    assert body["code"] == error_code
    assert body["request_id"] == response.headers["x-request-id"]
    assert body["message"]