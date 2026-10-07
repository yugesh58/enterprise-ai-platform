import time

from app.storage.database.query_executor import run_query


def execute_sql_node(state):
    start_time = time.perf_counter()

    sql_query = state["sql_query"]

    execution = run_query(sql_query)

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return {
        "result": execution["result"],
        "execution_error": execution["execution_error"],
        "error_type": execution["error_type"],
        "sql_execution_ms": elapsed_ms,
    }