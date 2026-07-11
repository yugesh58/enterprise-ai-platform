from dataclasses import dataclass, field
from typing import Any

@dataclass
class AgentResponse:
    answer: str
    status: str = "success"
    message: str = ""
    data: Any = None
    chart: Any = None
    citations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)