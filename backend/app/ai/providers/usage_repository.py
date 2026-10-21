
import logging
from decimal import Decimal
from typing import Any

from sqlalchemy import insert

from app.core.request_context import request_id_var
from app.models.llm_usage_event import llm_usage_events
from app.storage.database.connection import sql_engine

logger = logging.getLogger(__name__)


def persist_usage_event(
    *,
    operation: str,
    provider: str,
    model: str,
    duration_ms: float,
    outcome: str,
    usage: dict[str, int] | None = None,
    estimated_cost_usd: float | Decimal | None = None,
    chunk_count: int | None = None,
    error_type: str | None = None,
) -> None:
    """Persist one LLM operation without propagating database errors."""

    usage = usage or {}
    request_id = request_id_var.get()

    event: dict[str, Any] = {
        "request_id": request_id if request_id != "-" else None,
        "provider": provider,
        "model": model,
        "operation": operation,
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "estimated_cost_usd": (
            Decimal(str(estimated_cost_usd))
            if estimated_cost_usd is not None
            else None
        ),
        "duration_ms": Decimal(str(duration_ms)),
        "outcome": outcome,
        "error_type": error_type,
    }

    try:
        with sql_engine.begin() as connection:
            connection.execute(insert(llm_usage_events).values(**event))
    except Exception:
        # Observability must never break the model response.
        logger.exception("Failed to persist LLM usage event")
