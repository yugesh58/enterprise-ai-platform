from app.workflows.sql.generator import generate_sql


def generate_sql_node(state):

    question = state["question"]
    schema = state["schema"]
    memory = state["memory"]

    sql_query = generate_sql(
        question,
        schema,
        memory,
    )

    return {"sql_query": sql_query}
