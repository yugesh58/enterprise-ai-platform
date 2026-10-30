import asyncio
import time
import httpx
import pytest

from app.ai.providers import observability
from app.core.metrics import (
    LLM_REQUESTS_TOTAL,
    LLM_REQUEST_DURATION_SECONDS,
    LLM_TOKENS_TOTAL,
    LLM_ESTIMATED_COST_USD_TOTAL,
)


class FakeResponse:
    usage_metadata = {
        "input_tokens": 100,
        "output_tokens": 25,
        "total_tokens": 125,
    }
    response_metadata = {}


def metric_value(metric, **labels):
    return metric.labels(**labels)._value.get()


def histogram_sum(**labels):
    return LLM_REQUEST_DURATION_SECONDS.labels(**labels)._sum.get()


def delayed_response():
    time.sleep(0.002)
    return FakeResponse()


def test_sync_success_records_llm_metrics(monkeypatch):
    model = "prometheus-sync-test"
    labels = {
        "provider": "openai",
        "model": model,
        "operation": "invoke",
        "outcome": "success",
    }

    before_requests = metric_value(
        LLM_REQUESTS_TOTAL,
        **labels,
        error_type="none",
    )
    before_duration = histogram_sum(**labels)

    before_input = metric_value(
        LLM_TOKENS_TOTAL,
        provider="openai",
        model=model,
        token_type="input_tokens",
    )

    before_output = metric_value(
        LLM_TOKENS_TOTAL,
        provider="openai",
        model=model,
        token_type="output_tokens",
    )

    monkeypatch.setattr(
        observability,
        "_extract_cost_fields",
        lambda **kwargs: {"estimated_cost_usd": 0.01},
    )

    before_cost = metric_value(
        LLM_ESTIMATED_COST_USD_TOTAL,
        provider="openai",
        model=model,
    )

    response = observability.observe_invoke(
        operation="invoke",
        provider="openai",
        model=model,
        call=delayed_response,
    )

    assert isinstance(response, FakeResponse)

    assert metric_value(
        LLM_REQUESTS_TOTAL,
        **labels,
        error_type="none",
    ) == before_requests + 1

    assert metric_value(
        LLM_TOKENS_TOTAL,
        provider="openai",
        model=model,
        token_type="input_tokens",
    ) == before_input + 100

    assert metric_value(
        LLM_TOKENS_TOTAL,
        provider="openai",
        model=model,
        token_type="output_tokens",
    ) == before_output + 25

    assert metric_value(
        LLM_ESTIMATED_COST_USD_TOTAL,
        provider="openai",
        model=model,
    ) == before_cost + 0.01
    assert histogram_sum(**labels) > before_duration


def test_failed_sync_call_records_failure_metrics():
    model = "prometheus-failure-test"
    labels = {
        "provider": "openai",
        "model": model,
        "operation": "invoke",
        "outcome": "failure",
    }

    before = metric_value(
        LLM_REQUESTS_TOTAL,
        **labels,
        error_type="unknown",
    )
    before_duration = histogram_sum(**labels)

    def fail():
        time.sleep(0.002)
        raise RuntimeError("simulated failure")

    try:
        observability.observe_invoke(
            operation="invoke",
            provider="openai",
            model=model,
            call=fail,
        )
    except RuntimeError as exc:
        assert str(exc) == "simulated failure"
    else:
        pytest.fail("Expected RuntimeError")

    after = metric_value(
        LLM_REQUESTS_TOTAL,
        **labels,
        error_type="unknown",
    )

    assert after == before + 1
    assert histogram_sum(**labels) > before_duration


def test_async_success_records_llm_metrics(monkeypatch):
    model = "prometheus-async-success-test"
    labels = {
        "provider": "openai",
        "model": model,
        "operation": "ainvoke",
        "outcome": "success",
    }
    before_requests = metric_value(
        LLM_REQUESTS_TOTAL,
        **labels,
        error_type="none",
    )
    before_duration = histogram_sum(**labels)
    before_input = metric_value(
        LLM_TOKENS_TOTAL,
        provider="openai",
        model=model,
        token_type="input_tokens",
    )
    before_output = metric_value(
        LLM_TOKENS_TOTAL,
        provider="openai",
        model=model,
        token_type="output_tokens",
    )
    before_cost = metric_value(
        LLM_ESTIMATED_COST_USD_TOTAL,
        provider="openai",
        model=model,
    )

    monkeypatch.setattr(
        observability,
        "_extract_cost_fields",
        lambda **kwargs: {"estimated_cost_usd": 0.02},
    )

    async def fake_call():
        await asyncio.sleep(0.002)
        return FakeResponse()

    response = asyncio.run(
        observability.observe_ainvoke(
            operation="ainvoke",
            provider="openai",
            model=model,
            call=fake_call,
        )
    )

    assert isinstance(response, FakeResponse)
    assert metric_value(
        LLM_REQUESTS_TOTAL,
        **labels,
        error_type="none",
    ) == before_requests + 1
    assert metric_value(
        LLM_TOKENS_TOTAL,
        provider="openai",
        model=model,
        token_type="input_tokens",
    ) == before_input + 100
    assert metric_value(
        LLM_TOKENS_TOTAL,
        provider="openai",
        model=model,
        token_type="output_tokens",
    ) == before_output + 25
    assert metric_value(
        LLM_ESTIMATED_COST_USD_TOTAL,
        provider="openai",
        model=model,
    ) == before_cost + 0.02
    assert histogram_sum(**labels) > before_duration


def test_async_failure_records_failure_metrics():
    model = "prometheus-async-failure-test"
    labels = {
        "provider": "openai",
        "model": model,
        "operation": "ainvoke",
        "outcome": "failure",
    }
    before_requests = metric_value(
        LLM_REQUESTS_TOTAL,
        **labels,
        error_type="unknown",
    )
    before_duration = histogram_sum(**labels)

    async def fail():
        await asyncio.sleep(0.002)
        raise RuntimeError("simulated async failure")

    with pytest.raises(RuntimeError, match="simulated async failure"):
        asyncio.run(
            observability.observe_ainvoke(
                operation="ainvoke",
                provider="openai",
                model=model,
                call=fail,
            )
        )

    assert metric_value(
        LLM_REQUESTS_TOTAL,
        **labels,
        error_type="unknown",
    ) == before_requests + 1
    assert histogram_sum(**labels) > before_duration


def test_stream_success_records_llm_metrics(monkeypatch):
    model = "prometheus-stream-success-test"
    labels = {
        "provider": "openai",
        "model": model,
        "operation": "stream",
        "outcome": "success",
    }
    before = metric_value(
        LLM_REQUESTS_TOTAL,
        **labels,
        error_type="none",
    )
    before_duration = histogram_sum(**labels)
    before_input = metric_value(
        LLM_TOKENS_TOTAL,
        provider="openai",
        model=model,
        token_type="input_tokens",
    )
    before_output = metric_value(
        LLM_TOKENS_TOTAL,
        provider="openai",
        model=model,
        token_type="output_tokens",
    )
    before_cost = metric_value(
        LLM_ESTIMATED_COST_USD_TOTAL,
        provider="openai",
        model=model,
    )
    monkeypatch.setattr(
        observability,
        "_extract_cost_fields",
        lambda **kwargs: {"estimated_cost_usd": 0.03},
    )

    def delayed_chunks():
        time.sleep(0.002)
        yield FakeResponse()

    result = list(
        observability.observe_stream(
            provider="openai",
            model=model,
            chunks=delayed_chunks(),
        )
    )

    assert len(result) == 1
    assert isinstance(result[0], FakeResponse)

    after = metric_value(
        LLM_REQUESTS_TOTAL,
        **labels,
        error_type="none",
    )

    assert after == before + 1
    assert metric_value(
        LLM_TOKENS_TOTAL,
        provider="openai",
        model=model,
        token_type="input_tokens",
    ) == before_input + 100
    assert metric_value(
        LLM_TOKENS_TOTAL,
        provider="openai",
        model=model,
        token_type="output_tokens",
    ) == before_output + 25
    assert metric_value(
        LLM_ESTIMATED_COST_USD_TOTAL,
        provider="openai",
        model=model,
    ) == before_cost + 0.03
    assert histogram_sum(**labels) > before_duration


def test_stream_failure_records_failure_metrics():
    model = "prometheus-stream-failure-test"
    labels = {
        "provider": "openai",
        "model": model,
        "operation": "stream",
        "outcome": "failure",
    }
    before_requests = metric_value(
        LLM_REQUESTS_TOTAL,
        **labels,
        error_type="unknown",
    )
    before_duration = histogram_sum(**labels)
    before_input = metric_value(
        LLM_TOKENS_TOTAL,
        provider="openai",
        model=model,
        token_type="input_tokens",
    )
    before_output = metric_value(
        LLM_TOKENS_TOTAL,
        provider="openai",
        model=model,
        token_type="output_tokens",
    )

    def failing_chunks():
        time.sleep(0.002)
        yield FakeResponse()
        raise RuntimeError("simulated stream failure")

    with pytest.raises(RuntimeError, match="simulated stream failure"):
        list(
            observability.observe_stream(
                provider="openai",
                model=model,
                chunks=failing_chunks(),
            )
        )

    assert metric_value(
        LLM_REQUESTS_TOTAL,
        **labels,
        error_type="unknown",
    ) == before_requests + 1
    assert histogram_sum(**labels) > before_duration
    assert metric_value(
        LLM_TOKENS_TOTAL,
        provider="openai",
        model=model,
        token_type="input_tokens",
    ) == before_input + 100
    assert metric_value(
        LLM_TOKENS_TOTAL,
        provider="openai",
        model=model,
        token_type="output_tokens",
    ) == before_output + 25


def test_metrics_failure_does_not_interrupt_invocation(monkeypatch):
    class FailingCounter:
        def labels(self, **kwargs):
            raise RuntimeError("metrics backend unavailable")

    monkeypatch.setattr(
        observability,
        "LLM_REQUESTS_TOTAL",
        FailingCounter(),
    )

    response = observability.observe_invoke(
        operation="invoke",
        provider="openai",
        model="prometheus-metrics-failure-test",
        call=FakeResponse,
    )

    assert isinstance(response, FakeResponse)


def test_llm_duration_metric_is_recorded():
    model = "prometheus-duration-test"

    histogram = LLM_REQUEST_DURATION_SECONDS.labels(
        provider="openai",
        model=model,
        operation="invoke",
        outcome="success",
    )

    before = histogram._sum.get()

    observability.observe_invoke(
        operation="invoke",
        provider="openai",
        model=model,
        call=delayed_response,
    )

    assert histogram._sum.get() > before
def make_http_error(error_class, status_code):
    request = httpx.Request("POST", "https://example.com")
    response = httpx.Response(status_code, request=request)

    return error_class(
        "simulated error",
        response=response,
        body=None,
    )


@pytest.mark.parametrize(
    ("error_factory", "expected"),
    [
        (
            lambda: make_http_error(
                observability.RateLimitError, 429
            ),
            "rate_limit",
        ),
        (
            lambda: observability.APITimeoutError(
                request=httpx.Request("POST", "https://example.com")
            ),
            "timeout",
        ),
        (
            lambda: observability.APIConnectionError(
                message="Connection failed",
                request=httpx.Request("POST", "https://example.com"),
            ),
            "connection_error",
        ),
        (
            lambda: make_http_error(
                observability.AuthenticationError, 401
            ),
            "authentication_error",
        ),
        (
            lambda: make_http_error(
                observability.BadRequestError, 400
            ),
            "invalid_request",
        ),
        (
            lambda: RuntimeError("Unexpected error"),
            "unknown",
        ),
    ],
)
def test_llm_error_classification(error_factory, expected):
    error = error_factory()

    assert observability._classify_llm_error(error) == expected