from app.core.enums import ValidationStatus


ALLOWED_START = "SELECT"

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
    - Only SELECT statements are allowed.
    - No write, DDL, or database administration operations.
    """

    sql_query = state.get("sql_query", "").strip()

    if not sql_query:
        return {
            "validation_status": ValidationStatus.INVALID,
            "validation_reason": "SQL query is empty.",
        }

    # Remove one optional trailing semicolon.
    normalized_sql = sql_query.rstrip(";").strip()

    # A semicolon anywhere else means multiple statements.
    if ";" in normalized_sql:
        return {
            "validation_status": ValidationStatus.INVALID,
            "validation_reason": "Multiple SQL statements detected.",
        }

    sql_upper = normalized_sql.upper()

    # Only SELECT queries are allowed.
    if not sql_upper.startswith(ALLOWED_START):
        return {
            "validation_status": ValidationStatus.INVALID,
            "validation_reason": "Only SELECT statements are allowed.",
        }

    # Block dangerous SQL operations.
    tokens = sql_upper.replace("(", " ").replace(")", " ").split()

    for keyword in BLOCKED_KEYWORDS:
        if keyword in tokens:
            return {
                "validation_status": ValidationStatus.INVALID,
                "validation_reason": (
                    f"{keyword} statements are not allowed."
                ),
            }

    return {
        "validation_status": ValidationStatus.VALID,
        "validation_reason": "",
    }


def validation_router(state):
    """
    Route the workflow based on SQL validation.
    """

    if state["validation_status"] == ValidationStatus.VALID:
        return "execute_sql"

    if state.get("retry_count", 0) < 2:
        return "retry_sql"

    return "end"