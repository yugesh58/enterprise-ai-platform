
from sqlalchemy.exc import OperationalError

from app.core.enums import ExecutionErrorType
from app.storage.database import query_executor


def test_successful_query_execution(monkeypatch):
    expected_rows = [{"id": 1, "name": "Alice"}]

    class FakeDatabase:
        def fetch_all(self, query):
            assert "LIMIT" in query
            return expected_rows

    monkeypatch.setattr(
        query_executor.DatabaseFactory,
        "create",
        lambda _: FakeDatabase(),
    )

    result = query_executor.run_query("SELECT * FROM employees")

    assert result["result"] == expected_rows
    assert result["execution_error"] == ""
    assert result["error_type"] is None


def test_provider_creation_failure_is_handled(monkeypatch):
    def raise_connection_error(_):
        raise RuntimeError("connection details must not leak")

    monkeypatch.setattr(
        query_executor.DatabaseFactory,
        "create",
        raise_connection_error,
    )

    result = query_executor.run_query("SELECT 1")

    assert result["result"] == []
    assert result["error_type"] == ExecutionErrorType.UNKNOWN
    assert "connection details" not in result["execution_error"]


def test_statement_timeout_is_classified(monkeypatch):
    class FakeDatabase:
        def fetch_all(self, query):
            raise OperationalError(
                "SELECT 1",
                {},
                Exception("statement timeout"),
            )

    monkeypatch.setattr(
        query_executor.DatabaseFactory,
        "create",
        lambda _: FakeDatabase(),
    )

    result = query_executor.run_query("SELECT 1")

    assert result["error_type"] == ExecutionErrorType.TIMEOUT
    assert "execution time limit" in result["execution_error"]


def test_permission_error_is_classified(monkeypatch):
    class FakeDatabase:
        def fetch_all(self, query):
            raise OperationalError(
                "SELECT 1",
                {},
                Exception("permission denied"),
            )

    monkeypatch.setattr(
        query_executor.DatabaseFactory,
        "create",
        lambda _: FakeDatabase(),
    )

    result = query_executor.run_query("SELECT 1")

    assert result["error_type"] == ExecutionErrorType.PERMISSION
    assert "insufficient permissions" in result["execution_error"]


def test_generic_operational_error_is_classified(monkeypatch):
    class FakeDatabase:
        def fetch_all(self, query):
            raise OperationalError(
                "SELECT 1",
                {},
                Exception("database unavailable"),
            )

    monkeypatch.setattr(
        query_executor.DatabaseFactory,
        "create",
        lambda _: FakeDatabase(),
    )

    result = query_executor.run_query("SELECT 1")

    assert result["error_type"] == ExecutionErrorType.DATABASE
    assert result["execution_error"] == "A database operation failed."


def test_dbapi_error_is_sanitized(monkeypatch):
    from sqlalchemy.exc import DBAPIError

    class FakeDatabase:
        def fetch_all(self, query):
            raise DBAPIError(
                "SELECT 1",
                {},
                Exception("sensitive database details"),
            )

    monkeypatch.setattr(
        query_executor.DatabaseFactory,
        "create",
        lambda _: FakeDatabase(),
    )

    result = query_executor.run_query("SELECT 1")

    assert result["error_type"] == ExecutionErrorType.DATABASE
    assert "sensitive database details" not in result["execution_error"]


def test_unexpected_error_is_sanitized(monkeypatch):
    class FakeDatabase:
        def fetch_all(self, query):
            raise ValueError("sensitive internal details")

    monkeypatch.setattr(
        query_executor.DatabaseFactory,
        "create",
        lambda _: FakeDatabase(),
    )

    result = query_executor.run_query("SELECT 1")

    assert result["error_type"] == ExecutionErrorType.UNKNOWN
    assert "sensitive internal details" not in result["execution_error"]
def test_empty_query_is_rejected_without_database_access(monkeypatch):
    def unexpected_database_creation(_):
        raise AssertionError("Database should not be created")

    monkeypatch.setattr(
        query_executor.DatabaseFactory,
        "create",
        unexpected_database_creation,
    )

    result = query_executor.run_query("   ")

    assert result["result"] == []
    assert result["error_type"] == ExecutionErrorType.UNKNOWN
    assert result["execution_error"] == "SQL query is empty or invalid."


def test_trailing_semicolon_is_removed(monkeypatch):
    captured = {}

    class FakeDatabase:
        def fetch_all(self, query):
            captured["query"] = query
            return []

    monkeypatch.setattr(
        query_executor.DatabaseFactory,
        "create",
        lambda _: FakeDatabase(),
    )

    query_executor.run_query("SELECT * FROM employees;")

    assert "employees;" not in captured["query"]


def test_configured_result_limit_is_applied(monkeypatch):
    captured = {}

    class FakeDatabase:
        def fetch_all(self, query):
            captured["query"] = query
            return []

    monkeypatch.setattr(
        query_executor.DatabaseFactory,
        "create",
        lambda _: FakeDatabase(),
    )
    monkeypatch.setattr(query_executor.settings, "SQL_MAX_RESULT_ROWS", 25)

    query_executor.run_query("SELECT * FROM employees")

    assert "LIMIT 25" in captured["query"]


def test_cte_query_is_wrapped(monkeypatch):
    captured = {}

    class FakeDatabase:
        def fetch_all(self, query):
            captured["query"] = query
            return []

    monkeypatch.setattr(
        query_executor.DatabaseFactory,
        "create",
        lambda _: FakeDatabase(),
    )

    query_executor.run_query(
        "WITH active AS (SELECT * FROM employees) SELECT * FROM active"
    )

    assert "WITH active AS" in captured["query"]
    assert "LIMIT" in captured["query"]


def test_union_query_is_wrapped(monkeypatch):
    captured = {}

    class FakeDatabase:
        def fetch_all(self, query):
            captured["query"] = query
            return []

    monkeypatch.setattr(
        query_executor.DatabaseFactory,
        "create",
        lambda _: FakeDatabase(),
    )

    query_executor.run_query("SELECT 1 UNION SELECT 2")

    assert "UNION" in captured["query"]
    assert "LIMIT" in captured["query"]