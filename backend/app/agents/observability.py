import time
from collections.abc import Iterator
from typing import TypeVar
from app.core.enums import ResponseStatus
from app.core.logging import get_logger
from app.core.metrics import (
    AGENT_EXECUTIONS_TOTAL,
    AGENT_EXECUTION_DURATION_SECONDS,
)

logger = get_logger(__name__)

T = TypeVar("T")


def record_agent_execution(
    *,
    agent: str,
    operation: str,
    outcome: str,
    duration_seconds: float,
) -> None:
    """Record agent execution metrics without affecting execution."""
    try:
        AGENT_EXECUTIONS_TOTAL.labels(
            agent=agent,
            operation=operation,
            outcome=outcome,
        ).inc()

        AGENT_EXECUTION_DURATION_SECONDS.labels(
            agent=agent,
            operation=operation,
        ).observe(max(duration_seconds, 0.0))

    except Exception:
        logger.exception("Failed to record agent Prometheus metrics")


def observe_agent_execution(
    *,
    agent: str,
    operation: str,
    call,
) -> T:
    """Measure a synchronous agent execution."""
    start = time.perf_counter()
    outcome = "success"

    try:
        result = call()

        if getattr(result, "status", None) == ResponseStatus.FAILED:
            outcome = "failure"

        return result

    except Exception:
        outcome = "failure"
        raise

    finally:
        record_agent_execution(
            agent=agent,
            operation=operation,
            outcome=outcome,
            duration_seconds=time.perf_counter() - start,
        )

def observe_agent_stream(
    *,
    agent: str,
    chunks: Iterator[str],
) -> Iterator[str]:
    """Measure a streaming agent execution until completion or failure."""
    start = time.perf_counter()
    outcome = "success"

    try:
        yield from chunks
    except Exception:
        outcome = "failure"
        raise
    finally:
        record_agent_execution(
            agent=agent,
            operation="stream",
            outcome=outcome,
            duration_seconds=time.perf_counter() - start,
        )