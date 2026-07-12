from typing import Any
from typing_extensions import TypedDict

from app.contracts.agent_request import AgentRequest
from app.contracts.agent_response import AgentResponse
from app.core.request_context import RequestContext
from dataclasses import dataclass

@dataclass
class ValidationResult:
    is_valid: bool = False
    reason: str = ""

class SQLState(TypedDict):

    request: AgentRequest

    response: AgentResponse

    context: RequestContext

    schema: str

    sql_query: str

    validation: ValidationResult

    retry_count: int

    result: list[Any]