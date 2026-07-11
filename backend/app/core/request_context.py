from dataclasses import dataclass, field
from uuid import uuid4
from datetime import datetime


@dataclass
class RequestContext:

    request_id: str = field(default_factory=lambda: str(uuid4()))

    conversation_id: str | None = None

    user_id: str | None = None

    selected_agent: str | None = None

    model: str | None = None

    latency_ms: float = 0

    tokens_used: int = 0

    estimated_cost: float = 0

    reasoning: str = ""

    started_at: datetime = field(default_factory=datetime.utcnow)