from dataclasses import dataclass, field
from typing import Any

from app.core.enums import ResponseStatus


@dataclass(slots=True)
class AgentResponse:
    """
    Standard response returned by every agent.
    """

    answer: str

    status: ResponseStatus = ResponseStatus.SUCCESS

    message: str = ""

    data: Any = None

    chart: Any = None

    citations: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)