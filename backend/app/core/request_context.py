from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass(slots=True)
class RequestContext:
    """
    Carries request-specific metadata throughout the application.

    This object is created once per request and passed between
    the router, agents, workflows, and services.
    """

    request_id: str = field(default_factory=lambda: str(uuid4()))

    conversation_id: str | None = None

    user_id: str | None = None

    selected_agent: str | None = None

    model: str | None = None

    latency_ms: float = 0.0

    tokens_used: int = 0

    estimated_cost: float = 0.0

    reasoning: str = ""

    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
