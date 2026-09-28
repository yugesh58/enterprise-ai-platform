from app.storage.database.query_executor import run_query


def execute_sql_node(state):
    """
    Execute the validated SQL query.

    Database errors are captured in the workflow state so
    the SQL agent can retry instead of crashing.
    """

    sql_query = state["sql_query"]

    try:
        result = run_query(sql_query)

        return {
            "result": result,
            "execution_error": "",
        }

    except Exception as exc:
        return {
            "result": [],
            "execution_error": str(exc),
        }