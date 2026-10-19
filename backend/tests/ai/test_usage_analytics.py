
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.ai.providers.usage_analytics import (
    get_daily_usage,
    get_request_usage,
)


@patch("app.ai.providers.usage_analytics.sql_engine")
def test_get_daily_usage_returns_rows(mock_engine):
    expected = [
        {
            "usage_date": date(2026, 10, 19),
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "total_calls": 5,
            "failed_calls": 0,
            "total_input_tokens": 1025,
            "total_output_tokens": 82,
            "total_estimated_cost_usd": Decimal("0.0005412000"),
        }
    ]

    mock_connection = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_connection
    mock_connection.execute.return_value.mappings.return_value.all.return_value = (
        expected
    )

    result = get_daily_usage(days=7)

    assert result == expected
    mock_connection.execute.assert_called_once()


@pytest.mark.parametrize("days", [0, -1, 366])
def test_get_daily_usage_rejects_invalid_days(days):
    with pytest.raises(ValueError, match="days must be between 1 and 365"):
        get_daily_usage(days=days)


@patch("app.ai.providers.usage_analytics.sql_engine")
def test_get_request_usage_returns_rows(mock_engine):
    expected = [
        {
            "request_id": "test-request",
            "operation": "invoke",
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "total_calls": 1,
            "failed_calls": 0,
            "total_input_tokens": 100,
            "total_output_tokens": 20,
            "total_estimated_cost_usd": Decimal("0.000072"),
            "total_duration_ms": Decimal("125.50"),
        }
    ]

    mock_connection = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_connection
    mock_connection.execute.return_value.mappings.return_value.all.return_value = (
        expected
    )

    result = get_request_usage("test-request")

    assert result == expected
    mock_connection.execute.assert_called_once_with(
        mock_connection.execute.call_args.args[0],
        {"request_id": "test-request"},
    )
