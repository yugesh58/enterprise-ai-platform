
from unittest.mock import MagicMock

from app.ai.providers import usage_repository
from app.core.request_context import request_id_var


def test_persist_usage_event_includes_request_id(monkeypatch):
    expected_request_id = "ce9b2113-493e-48b2-b4e5-b45d72c65a91"
    captured = {}

    mock_connection = MagicMock()

    def capture_insert(statement):
        captured["statement"] = statement
        return statement

    def capture_values(**values):
        captured.update(values)
        return object()

    mock_table_insert = MagicMock()
    mock_table_insert.values.side_effect = capture_values

    monkeypatch.setattr(
        usage_repository,
        "insert",
        lambda table: mock_table_insert,
    )

    mock_engine = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_connection
    mock_connection.execute.return_value = None

    monkeypatch.setattr(usage_repository, "sql_engine", mock_engine)

    token = request_id_var.set(expected_request_id)
    try:
        usage_repository.persist_usage_event(
            operation="invoke",
            provider="openai",
            model="test-model",
            duration_ms=125.0,
            outcome="success",
        )
    finally:
        request_id_var.reset(token)

    assert captured["request_id"] == expected_request_id
    assert captured["outcome"] == "success"
