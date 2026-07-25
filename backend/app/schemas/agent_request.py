from dataclasses import dataclass, field
from typing import Any

from app.core.request_context import RequestContext


@dataclass(slots=True)
class AgentRequest:
    """
    Represents an incoming request passed to an agent.
    """

    question: str

    context: RequestContext = field(default_factory=RequestContext)

    chat_history: list[str] = field(default_factory=list)

    uploaded_files: list[Any] = field(default_factory=list)

    attributes: dict[str, Any] = field(default_factory=dict)
