from app.core.enums import ExecutionErrorType
from app.workflows.sql.graph import execution_router


def test_success_routes_to_summarize():
    state = {
        "execution_error": "",
        "error_type": None,
        "retry_count": 0,
    }

    assert execution_router(state) == "summarize"


def test_database_error_retries():
    state = {
        "execution_error": "relation does not exist",
        "error_type": ExecutionErrorType.DATABASE,
        "retry_count": 0,
    }

    assert execution_router(state) == "retry_sql"


def test_database_error_retries_second_time():
    state = {
        "execution_error": "syntax error",
        "error_type": ExecutionErrorType.DATABASE,
        "retry_count": 1,
    }

    assert execution_router(state) == "retry_sql"


def test_database_error_stops_after_two_retries():
    state = {
        "execution_error": "syntax error",
        "error_type": ExecutionErrorType.DATABASE,
        "retry_count": 2,
    }

    assert execution_router(state) == "end"


def test_timeout_stops_immediately():
    state = {
        "execution_error": "statement timeout",
        "error_type": ExecutionErrorType.TIMEOUT,
        "retry_count": 0,
    }

    assert execution_router(state) == "end"


def test_timeout_does_not_retry():
    state = {
        "execution_error": "statement timeout",
        "error_type": ExecutionErrorType.TIMEOUT,
        "retry_count": 1,
    }

    assert execution_router(state) == "end"


def test_permission_error_stops_immediately():
    state = {
        "execution_error": "permission denied",
        "error_type": ExecutionErrorType.PERMISSION,
        "retry_count": 0,
    }

    assert execution_router(state) == "end"


def test_permission_error_does_not_retry():
    state = {
        "execution_error": "permission denied",
        "error_type": ExecutionErrorType.PERMISSION,
        "retry_count": 1,
    }

    assert execution_router(state) == "end"


def test_unknown_error_retries():
    state = {
        "execution_error": "unexpected database failure",
        "error_type": ExecutionErrorType.UNKNOWN,
        "retry_count": 0,
    }

    assert execution_router(state) == "retry_sql"
