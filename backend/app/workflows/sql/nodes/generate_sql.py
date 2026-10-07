import time

from app.workflows.sql.generator import generate_sql


def generate_sql_node(state):
    start_time = time.perf_counter()

    question = state["question"]
    schema = state["schema"]
    memory = state["memory"]

    sql_query = generate_sql(
        question,
        schema,
        memory,
    )

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return {
        "sql_query": sql_query,
        "sql_generation_ms": elapsed_ms,
    }