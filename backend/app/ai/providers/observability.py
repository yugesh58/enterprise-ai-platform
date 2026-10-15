
import time
from collections.abc import AsyncIterator, Iterator
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


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
            if isinstance(value, int):
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
                if target not in usage and isinstance(value, int):
                    usage[target] = value

    return usage


def observe_invoke(
    operation: str,
    provider: str,
    model: str,
    call: Any,
) -> Any:
    """Observe a synchronous model invocation."""
    start = time.perf_counter()

    try:
        response = call()
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            "LLM call completed",
            extra={
                "operation": operation,
                "provider": provider,
                "model": model,
                "duration_ms": duration_ms,
                "outcome": "success",
                **_extract_token_usage(response),
            },
        )
        return response
    except Exception:
        logger.exception(
            "LLM call failed",
            extra={
                "operation": operation,
                "provider": provider,
                "model": model,
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                "outcome": "failure",
            },
        )
        raise


async def observe_ainvoke(
    operation: str,
    provider: str,
    model: str,
    call: Any,
) -> Any:
    """Observe an asynchronous model invocation."""
    start = time.perf_counter()

    try:
        response = await call()
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            "LLM call completed",
            extra={
                "operation": operation,
                "provider": provider,
                "model": model,
                "duration_ms": duration_ms,
                "outcome": "success",
                **_extract_token_usage(response),
            },
        )
        return response
    except Exception:
        logger.exception(
            "LLM call failed",
            extra={
                "operation": operation,
                "provider": provider,
                "model": model,
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                "outcome": "failure",
            },
        )
        raise


def observe_stream(
    provider: str,
    model: str,
    chunks: Iterator[Any],
) -> Iterator[Any]:
    """Observe a synchronous stream for its entire iteration."""
    start = time.perf_counter()
    chunk_count = 0

    try:
        for chunk in chunks:
            chunk_count += 1
            yield chunk

        logger.info(
            "LLM stream completed",
            extra={
                "operation": "stream",
                "provider": provider,
                "model": model,
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                "chunk_count": chunk_count,
                "outcome": "success",
            },
        )
    except Exception:
        logger.exception(
            "LLM stream failed",
            extra={
                "operation": "stream",
                "provider": provider,
                "model": model,
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                "chunk_count": chunk_count,
                "outcome": "failure",
            },
        )
        raise
