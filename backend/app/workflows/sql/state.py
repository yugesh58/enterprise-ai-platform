from typing_extensions import TypedDict

class SQLState(TypedDict):
    question: str
    memory:list
    summary:str
    schema: str
    sql_query: str
    validation_status: str
    validation_reason: str
    retry_count: int
    result: list