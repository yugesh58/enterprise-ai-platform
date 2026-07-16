from app.core.enums import ValidationStatus




def validate_sql_node(state):
    """
    Validate the generated SQL query before execution.
    """

    sql_query = state["sql_query"].strip()

    # Prevent multiple SQL statements
    if ";" in sql_query[:-1]:
        return {
            "validation_status": ValidationStatus.INVALID,
            "validation_reason": "Multiple SQL statements detected.",
        }

    dangerous_keywords = [
        "DROP",
        "DELETE",
        "TRUNCATE",
        "UPDATE",
        "ALTER",
        "INSERT",
    ]

    sql_upper = sql_query.upper()

    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return {
                "validation_status": ValidationStatus.INVALID,
                "validation_reason": f"{keyword} statements are not allowed.",
            }

    if not sql_upper.startswith("SELECT"):
        return {
            "validation_status": ValidationStatus.INVALID,
            "validation_reason": "Only SELECT statements are allowed.",
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