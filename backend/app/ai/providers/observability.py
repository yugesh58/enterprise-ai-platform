
import asyncio
import time
from collections.abc import Iterator
from typing import Any

from app.ai.providers.cost_calculator import (
    calculate_llm_cost,
    get_configured_model_pricing,
)
from app.ai.providers.usage_repository import persist_usage_event
from app.core.logging import get_logger
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)

logger = get_logger(__name__)
def _classify_llm_error(exc: Exception) -> str:
    """Map provider exceptions to stable diagnostic categories."""
    if isinstance(exc, RateLimitError):
        return "rate_limit"
    if isinstance(exc, APITimeoutError):
        return "timeout"
    if isinstance(exc, APIConnectionError):
        return "connection_error"
    if isinstance(exc, AuthenticationError):
        return "authentication_error"
    if isinstance(exc, BadRequestError):
        return "invalid_request"
    return "unknown"


def _extract_token_usage(response: Any) -> dict[str, int]:
    """Extract token usage from a LangChain response when available."""
    usage: dict[str, int] = {}

    usage_metadata = getattr(response, "usage_metadata", None)
    if isinstance(usage_metadata, dict):
        for source, target in (
            ("input_tokens", "input_tokens"),
            ("output_tokens", "output_tokens"),
            ("total_tokens", "total_tokens"),
        ):
            value = usage_metadata.get(source)
            if isinstance(value, int) and not isinstance(value, bool):
                usage[target] = value

    response_metadata = getattr(response, "response_metadata", None)
    if isinstance(response_metadata, dict):
        token_usage = response_metadata.get("token_usage")

        if not isinstance(token_usage, dict):
            token_usage = response_metadata.get("usage")

        if isinstance(token_usage, dict):
            aliases = {
                "prompt_tokens": "input_tokens",
                "completion_tokens": "output_tokens",
                "total_tokens": "total_tokens",
                "input_tokens": "input_tokens",
                "output_tokens": "output_tokens",
            }

            for source, target in aliases.items():
                value = token_usage.get(source)

                if (
                    target not in usage
                    and isinstance(value, int)
                    and not isinstance(value, bool)
                ):
                    usage[target] = value

    return usage


def _extract_cost_fields(
    *,
    provider: str,
    model: str,
    usage: dict[str, int],
) -> dict[str, float]:
    """Calculate estimated USD cost when pricing and token usage exist."""
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")

    if input_tokens is None or output_tokens is None:
        return {}

    pricing = get_configured_model_pricing(
        provider=provider,
        model=model,
    )

    cost = calculate_llm_cost(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        pricing=pricing,
    )

    if cost is None:
        return {}

    return {"estimated_cost_usd": float(cost)}


def _persist_event_safely(
    *,
    operation: str,
    provider: str,
    model: str,
    duration_ms: float,
    outcome: str,
    usage: dict[str, int] | None = None,
    cost_fields: dict[str, float] | None = None,
    error_type: str | None = None,
) -> None:
    """Persist telemetry without affecting model execution."""
    try:
        persist_usage_event(
            operation=operation,
            provider=provider,
            model=model,
            duration_ms=duration_ms,
            outcome=outcome,
            usage=usage,
            estimated_cost_usd=(cost_fields or {}).get(
                "estimated_cost_usd"
            ),
            error_type=error_type,
        )
    except Exception:
        logger.exception("Unexpected error while persisting LLM telemetry")


async def _persist_event_async(**event: Any) -> None:
    """Run synchronous database persistence outside the event loop."""
    await asyncio.to_thread(_persist_event_safely, **event)


def observe_invoke(
    operation: str,
    provider: str,
    model: str,
    call: Any,  
    ) -> Any:
    """Observe and persist a synchronous model invocation."""
    start = time.perf_counter()

    try:
        response = call()
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        usage = _extract_token_usage(response)
        cost_fields = _extract_cost_fields(
            provider=provider,
            model=model,
            usage=usage,
        )

        logger.info(
            "LLM call completed",
            extra={
                "operation": operation,
                "provider": provider,
                "model": model,
                "duration_ms": duration_ms,
                "outcome": "success",
                **usage,
                **cost_fields,
            },
        )

        _persist_event_safely(
            operation=operation,
            provider=provider,
            model=model,
            duration_ms=duration_ms,
            outcome="success",
            usage=usage,
            cost_fields=cost_fields,
        )

        return response

    except Exception as exc:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        error_type = _classify_llm_error(exc)

        logger.exception(
            "LLM call failed",
            extra={
                "operation": operation,
                "provider": provider,
                "model": model,
                "duration_ms": duration_ms,
                "outcome": "failure",
                "error_type": error_type,
            },
        )

        _persist_event_safely(
            operation=operation,
            provider=provider,
            model=model,
            duration_ms=duration_ms,
            outcome="failure",
            error_type=error_type,
        )

        raise


async def observe_ainvoke(
    operation: str,
    provider: str,
    model: str,
    call: Any,
) -> Any:
    """Observe and persist an asynchronous model invocation."""
    start = time.perf_counter()

    try:
        response = await call()
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        usage = _extract_token_usage(response)
        cost_fields = _extract_cost_fields(
            provider=provider,
            model=model,
            usage=usage,
        )

        logger.info(
            "LLM call completed",
            extra={
                "operation": operation,
                "provider": provider,
                "model": model,
                "duration_ms": duration_ms,
                "outcome": "success",
                **usage,
                **cost_fields,
            },
        )

        await _persist_event_async(
            operation=operation,
            provider=provider,
            model=model,
            duration_ms=duration_ms,
            outcome="success",
            usage=usage,
            cost_fields=cost_fields,
        )

        return response

    except Exception as exc:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        error_type = _classify_llm_error(exc)

        logger.exception(
            "LLM call failed",
            extra={
                "operation": operation,
                "provider": provider,
                "model": model,
                "duration_ms": duration_ms,
                "outcome": "failure",
                "error_type": error_type,
            },
        )

        await _persist_event_async(
            operation=operation,
            provider=provider,
            model=model,
            duration_ms=duration_ms,
            outcome="failure",
            error_type=error_type,
        )

        raise


def observe_stream(
    provider: str,
    model: str,
    chunks: Iterator[Any],
) -> Iterator[Any]:
    """Observe and persist stream duration, chunks, usage, and cost."""
    start = time.perf_counter()
    chunk_count = 0
    usage: dict[str, int] = {}

    try:
        for chunk in chunks:
            chunk_count += 1

            # Usage metadata is commonly attached to the final chunk.
            chunk_usage = _extract_token_usage(chunk)
            usage.update(chunk_usage)

            yield chunk

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        cost_fields = _extract_cost_fields(
            provider=provider,
            model=model,
            usage=usage,
        )

        logger.info(
            "LLM stream completed",
            extra={
                "operation": "stream",
                "provider": provider,
                "model": model,
                "duration_ms": duration_ms,
                "chunk_count": chunk_count,
                "outcome": "success",
                **usage,
                **cost_fields,
            },
        )

        _persist_event_safely(
            operation="stream",
            provider=provider,
            model=model,
            duration_ms=duration_ms,
            outcome="success",
            usage=usage,
            cost_fields=cost_fields,
        )

    except Exception as exc:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        cost_fields = _extract_cost_fields(
            provider=provider,
            model=model,
            usage=usage,
        )
        error_type = _classify_llm_error(exc)

        logger.exception(
            "LLM stream failed",
            extra={
                "operation": "stream",
                "provider": provider,
                "model": model,
                "duration_ms": duration_ms,
                "chunk_count": chunk_count,
                "outcome": "failure",
                **usage,
                **cost_fields,
                "error_type": error_type,
            },
        )

        _persist_event_safely(
            operation="stream",
            provider=provider,
            model=model,
            duration_ms=duration_ms,
            outcome="failure",
            usage=usage,
            cost_fields=cost_fields,
            error_type=error_type,
        )

        raise

def test_observe_stream_persists_error_type(monkeypatch):
    """Stream failure telemetry includes the classified error type."""

    from app.ai.providers import observability

    persisted_events = []

    monkeypatch.setattr(
        observability,
        "_persist_event_safely",
        lambda **kwargs: persisted_events.append(kwargs),
    )

    def failing_chunks():
        yield "first chunk"
        raise RuntimeError("simulated stream failure")

    with pytest.raises(RuntimeError, match="simulated stream failure"):
        list(
            observe_stream(
                provider="openai",
                model="test-model",
                chunks=failing_chunks(),
            )
        )

    assert len(persisted_events) == 1
    assert persisted_events[0]["outcome"] == "failure"
    assert persisted_events[0]["error_type"] == "unknown"
    assert persisted_events[0]["operation"] == "stream"
    assert persisted_events[0]["chunk_count"] == 1
