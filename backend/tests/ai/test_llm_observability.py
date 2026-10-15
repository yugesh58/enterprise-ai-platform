import asyncio
import logging

import pytest

from app.ai.providers.observability import (
    observe_ainvoke,
    observe_invoke,
    observe_stream,
)


class FakeResponse:
    """Mock LLM response containing token usage metadata."""

    usage_metadata = {
        "input_tokens": 12,
        "output_tokens": 8,
        "total_tokens": 20,
    }
    response_metadata = {}


def test_observe_invoke_logs_latency_and_token_usage(caplog):
    """Successful synchronous calls log latency and token usage."""

    with caplog.at_level(
        logging.INFO,
        logger="app.ai.providers.observability",
    ):
        response = observe_invoke(
            operation="invoke",
            provider="openai",
            model="test-model",
            call=lambda: FakeResponse(),
        )

    assert isinstance(response, FakeResponse)

    record = next(
        r for r in caplog.records
        if r.message == "LLM call completed"
    )

    assert record.provider == "openai"
    assert record.model == "test-model"
    assert record.operation == "invoke"
    assert record.duration_ms >= 0
    assert record.outcome == "success"
    assert record.input_tokens == 12
    assert record.output_tokens == 8
    assert record.total_tokens == 20


def test_observe_invoke_logs_failure_and_reraises(caplog):
    """Failed synchronous calls log the failure and re-raise."""

    def fail():
        raise RuntimeError("simulated provider failure")

    with caplog.at_level(
        logging.ERROR,
        logger="app.ai.providers.observability",
    ):
        with pytest.raises(
            RuntimeError,
            match="simulated provider failure",
        ):
            observe_invoke(
                operation="invoke",
                provider="openai",
                model="test-model",
                call=fail,
            )

    record = next(
        r for r in caplog.records
        if r.message == "LLM call failed"
    )

    assert record.provider == "openai"
    assert record.model == "test-model"
    assert record.operation == "invoke"
    assert record.duration_ms >= 0
    assert record.outcome == "failure"


def test_observe_stream_logs_duration_and_chunk_count(caplog):
    """Successful streams log their duration and number of chunks."""

    chunks = iter(["chunk-1", "chunk-2", "chunk-3"])

    with caplog.at_level(
        logging.INFO,
        logger="app.ai.providers.observability",
    ):
        result = list(
            observe_stream(
                provider="openai",
                model="test-model",
                chunks=chunks,
            )
        )

    assert result == ["chunk-1", "chunk-2", "chunk-3"]

    record = next(
        r for r in caplog.records
        if r.message == "LLM stream completed"
    )

    assert record.provider == "openai"
    assert record.model == "test-model"
    assert record.operation == "stream"
    assert record.chunk_count == 3
    assert record.duration_ms >= 0
    assert record.outcome == "success"


def test_observe_stream_logs_failure_and_reraises(caplog):
    """Stream failures are logged and propagated to the caller."""

    def failing_chunks():
        yield "chunk-1"
        raise RuntimeError("simulated stream failure")

    with caplog.at_level(
        logging.ERROR,
        logger="app.ai.providers.observability",
    ):
        with pytest.raises(
            RuntimeError,
            match="simulated stream failure",
        ):
            list(
                observe_stream(
                    provider="openai",
                    model="test-model",
                    chunks=failing_chunks(),
                )
            )

    record = next(
        r for r in caplog.records
        if r.message == "LLM stream failed"
    )

    assert record.provider == "openai"
    assert record.model == "test-model"
    assert record.duration_ms >= 0
    assert record.chunk_count == 1
    assert record.outcome == "failure"


def test_observe_ainvoke_logs_latency_and_token_usage(caplog):
    """Successful asynchronous calls log latency and token usage."""

    async def run_test():
        async def fake_call():
            return FakeResponse()

        with caplog.at_level(
            logging.INFO,
            logger="app.ai.providers.observability",
        ):
            response = await observe_ainvoke(
                operation="ainvoke",
                provider="azure",
                model="test-deployment",
                call=fake_call,
            )

        assert isinstance(response, FakeResponse)

        record = next(
            r for r in caplog.records
            if r.message == "LLM call completed"
        )

        assert record.provider == "azure"
        assert record.model == "test-deployment"
        assert record.operation == "ainvoke"
        assert record.duration_ms >= 0
        assert record.outcome == "success"
        assert record.input_tokens == 12
        assert record.output_tokens == 8
        assert record.total_tokens == 20

    asyncio.run(run_test())


def test_observe_ainvoke_logs_failure_and_reraises(caplog):
    """Asynchronous failures are logged and propagated."""

    async def run_test():
        async def fail():
            raise RuntimeError("simulated async failure")

        with caplog.at_level(
            logging.ERROR,
            logger="app.ai.providers.observability",
        ):
            with pytest.raises(
                RuntimeError,
                match="simulated async failure",
            ):
                await observe_ainvoke(
                    operation="ainvoke",
                    provider="azure",
                    model="test-deployment",
                    call=fail,
                )

        record = next(
            r for r in caplog.records
            if r.message == "LLM call failed"
        )

        assert record.provider == "azure"
        assert record.model == "test-deployment"
        assert record.operation == "ainvoke"
        assert record.duration_ms >= 0
        assert record.outcome == "failure"

    asyncio.run(run_test())


def test_observability_does_not_log_prompt_or_response(caplog):
    """Prompts and generated response content must not appear in logs."""

    secret_prompt = "private-prompt-DO-NOT-LOG"
    secret_response = "private-response-DO-NOT-LOG"

    with caplog.at_level(
        logging.INFO,
        logger="app.ai.providers.observability",
    ):
        observe_invoke(
            operation="invoke",
            provider="openai",
            model="test-model",
            call=lambda: secret_response,
        )

    assert secret_prompt not in caplog.text
    assert secret_response not in caplog.text
