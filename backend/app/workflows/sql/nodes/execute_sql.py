from app.storage.database.query_executor import run_query


def execute_sql_node(state):
    """
    Execute the validated SQL query.
    """

    sql_query = state["sql_query"]

    execution = run_query(sql_query)

    return {
        "result": execution["result"],
        "execution_error": execution["execution_error"],
    }