import time

from app.core.enums import ValidationStatus


BLOCKED_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "REPLACE",
    "MERGE",
    "UPSERT",
    "GRANT",
    "REVOKE",
    "ATTACH",
    "DETACH",
    "VACUUM",
    "PRAGMA",
}


def validate_sql_node(state):
    """
    Validate LLM-generated SQL before execution.

    Policy:
    - Exactly one SQL statement.
    - Only SELECT/WITH read queries are allowed.
    - No write, DDL, or database administration operations.
    - SQL comments are not allowed.
    """

    start_time = time.perf_counter()

    sql_query = state.get("sql_query", "").strip()

    def result(status, reason):
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return {
            "validation_status": status,
            "validation_reason": reason,
            "sql_validation_ms": elapsed_ms,
        }

    if not sql_query:
        return result(
            ValidationStatus.INVALID,
            "SQL query is empty.",
        )

    normalized_sql = sql_query.rstrip(";").strip()

    if (
        "--" in normalized_sql
        or "/*" in normalized_sql
        or "*/" in normalized_sql
    ):
        return result(
            ValidationStatus.INVALID,
            "SQL comments are not allowed.",
        )

    if ";" in normalized_sql:
        return result(
            ValidationStatus.INVALID,
            "Multiple SQL statements detected.",
        )

    sql_upper = normalized_sql.upper()

    if not (
        sql_upper.startswith("SELECT")
        or sql_upper.startswith("WITH")
    ):
        return result(
            ValidationStatus.INVALID,
            "Only SELECT statements are allowed.",
        )

    tokens = (
        sql_upper
        .replace("(", " ")
        .replace(")", " ")
        .split()
    )

    for keyword in BLOCKED_KEYWORDS:
        if keyword in tokens:
            return result(
                ValidationStatus.INVALID,
                f"{keyword} statements are not allowed.",
            )

    return result(
        ValidationStatus.VALID,
        "",
    )


def validation_router(state):
    """
    Route the workflow based on SQL validation.
    """

    if state["validation_status"] == ValidationStatus.VALID:
        return "execute_sql"

    if state.get("retry_count", 0) < 2:
        return "retry_sql"

    return "end"