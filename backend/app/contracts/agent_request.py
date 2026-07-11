from dataclasses import dataclass,field
from typing import Any

from app.core.request_context import RequestContext

@dataclass
class AgentRequest:
    question: str

    context: RequestContext=field(default_factory=RequestContext)

    chat_history: list[str] = field(default_factory=list)

    uploaded_files: list[Any] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)