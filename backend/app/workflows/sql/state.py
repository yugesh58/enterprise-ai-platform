from typing_extensions import TypedDict


class SQLState(TypedDict):
    conversation_id: str

    question: str
    memory: list

    summary: str
    answer: str

    schema: dict
    sql_query: str

    validation_status: str
    validation_reason: str

    execution_error: str
    error_type: str | None

    retry_count: int

    result: list

    # Execution metrics
    schema_retrieval_ms: float
    sql_generation_ms: float
    sql_validation_ms: float
    sql_execution_ms: float
    summarization_ms: float
    total_latency_ms: float