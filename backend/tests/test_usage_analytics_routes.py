
from unittest.mock import patch


from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

REQUEST_ID = "ce9b2113-493e-48b2-b4e5-b45d72c65a91"


def test_daily_usage_returns_analytics():
    expected = [
        {
            "usage_date": "2026-10-19",
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "total_calls": 5,
            "failed_calls": 0,
            "total_input_tokens": 1025,
            "total_output_tokens": 82,
            "total_estimated_cost_usd": "0.0005412000",
            "error_types": [],
        }
    ]

    with patch(
        "app.api.routes.usage_analytics.get_daily_usage",
        return_value=expected,
    ) as mock_get_daily_usage:
        response = client.get(
            "/analytics/llm-usage/daily",
            params={"days": 7},
        )

    assert response.status_code == 200
    assert response.json() == expected
    mock_get_daily_usage.assert_called_once_with(days=7)


def test_request_usage_returns_aggregated_analytics():
    expected = [
        {
            "request_id": REQUEST_ID,
            "operation": "invoke",
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "total_calls": 2,
            "failed_calls": 0,
            "total_input_tokens": 725,
            "total_output_tokens": 22,
            "total_estimated_cost_usd": "0.0003252000",
            "total_duration_ms": "3388.27",
            "error_types": [],
        }
    ]

    with patch(
        "app.api.routes.usage_analytics.get_request_usage",
        return_value=expected,
    ) as mock_get_request_usage:
        response = client.get(
            f"/analytics/llm-usage/requests/{REQUEST_ID}"
        )

    assert response.status_code == 200
    assert response.json() == expected
    mock_get_request_usage.assert_called_once_with(REQUEST_ID)


def test_daily_usage_rejects_days_below_minimum():
    with patch(
        "app.api.routes.usage_analytics.get_daily_usage"
    ) as mock_get_daily_usage:
        response = client.get(
            "/analytics/llm-usage/daily",
            params={"days": 0},
        )

    assert response.status_code == 422
    assert response.headers.get("x-request-id")
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    mock_get_daily_usage.assert_not_called()


def test_daily_usage_rejects_days_above_maximum():
    with patch(
        "app.api.routes.usage_analytics.get_daily_usage"
    ) as mock_get_daily_usage:
        response = client.get(
            "/analytics/llm-usage/daily",
            params={"days": 366},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    mock_get_daily_usage.assert_not_called()


def test_request_usage_rejects_invalid_uuid():
    with patch(
        "app.api.routes.usage_analytics.get_request_usage"
    ) as mock_get_request_usage:
        response = client.get(
            "/analytics/llm-usage/requests/not-a-uuid"
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    mock_get_request_usage.assert_not_called()

def test_daily_usage_service_failure_returns_standard_error():
    with patch(
        "app.api.routes.usage_analytics.get_daily_usage",
        side_effect=RuntimeError("database connection details"),
    ):
        response = client.get("/analytics/llm-usage/daily")

    assert response.status_code == 500
    assert response.headers.get("x-request-id")
    assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert response.json()["error"]["message"] == (
        "An unexpected error occurred."
    )
    assert "database connection details" not in response.text


def test_request_usage_service_failure_returns_standard_error():
    with patch(
        "app.api.routes.usage_analytics.get_request_usage",
        side_effect=RuntimeError("database connection details"),
    ):
        response = client.get(
            f"/analytics/llm-usage/requests/{REQUEST_ID}"
        )

    assert response.status_code == 500
    assert response.headers.get("x-request-id")
    assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert response.json()["error"]["message"] == (
        "An unexpected error occurred."
    )
    assert "database connection details" not in response.text