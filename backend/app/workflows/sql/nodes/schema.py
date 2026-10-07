import time

from app.storage.database.schema_retriever import get_relevant_schema


def retrieve_schema_node(state):
    start_time = time.perf_counter()

    question = state["question"]

    schema = get_relevant_schema(question)

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return {
        "schema": schema,
        "schema_retrieval_ms": elapsed_ms,
    }