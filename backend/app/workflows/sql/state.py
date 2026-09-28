from typing_extensions import TypedDict


class SQLState(TypedDict):
    question: str
    memory: list
    summary: str
    answer: str
    schema: str
    sql_query: str
    validation_status: str
    validation_reason: str
    execution_error: str
    retry_count: int
    result: list