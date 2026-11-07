import pytest

from app.agents.observability import (
    observe_agent_execution,
    observe_agent_stream,
)
from app.core.metrics import (
    AGENT_EXECUTIONS_TOTAL,
    AGENT_EXECUTION_DURATION_SECONDS,
)
from app.core.enums import ResponseStatus
from app.schemas.agent_response import AgentResponse

def metric_value(metric, **labels):
    return metric.labels(**labels)._value.get()


def test_records_successful_agent_execution():
    labels = {
        "agent": "test",
        "operation": "execute",
        "outcome": "success",
    }

    before = metric_value(AGENT_EXECUTIONS_TOTAL, **labels)

    result = observe_agent_execution(
        agent="test",
        operation="execute",
        call=lambda: "success",
    )

    assert result == "success"
    assert metric_value(AGENT_EXECUTIONS_TOTAL, **labels) == before + 1


def test_records_failed_agent_execution():
    labels = {
        "agent": "test",
        "operation": "execute",
        "outcome": "failure",
    }

    before = metric_value(AGENT_EXECUTIONS_TOTAL, **labels)

    with pytest.raises(RuntimeError):
        observe_agent_execution(
            agent="test",
            operation="execute",
            call=lambda: (_ for _ in ()).throw(RuntimeError("failed")),
        )

    assert metric_value(AGENT_EXECUTIONS_TOTAL, **labels) == before + 1


def test_records_stream_after_completion():
    labels = {
        "agent": "test",
        "operation": "stream",
        "outcome": "success",
    }

    before = metric_value(AGENT_EXECUTIONS_TOTAL, **labels)

    result = list(
        observe_agent_stream(
            agent="test",
            chunks=iter(["hello", " world"]),
        )
    )

    assert result == ["hello", " world"]
    assert metric_value(AGENT_EXECUTIONS_TOTAL, **labels) == before + 1


def test_records_stream_failure():
    labels = {
        "agent": "test",
        "operation": "stream",
        "outcome": "failure",
    }

    before = metric_value(AGENT_EXECUTIONS_TOTAL, **labels)

    def failing_stream():
        yield "partial"
        raise RuntimeError("stream failed")

    with pytest.raises(RuntimeError):
        list(
            observe_agent_stream(
                agent="test",
                chunks=failing_stream(),
            )
        )

    assert metric_value(AGENT_EXECUTIONS_TOTAL, **labels) == before + 1


def test_records_execution_duration():
    labels = {
        "agent": "test",
        "operation": "execute",
    }

    histogram = AGENT_EXECUTION_DURATION_SECONDS.labels(**labels)
    before = histogram.collect()[0].samples

    before_count = next(
        sample.value
        for sample in before
        if sample.name.endswith("_count")
    )

    observe_agent_execution(
        agent="test",
        operation="execute",
        call=lambda: "done",
    )

    after = histogram.collect()[0].samples

    after_count = next(
        sample.value
        for sample in after
        if sample.name.endswith("_count")
    )

    assert after_count == before_count + 1

def test_records_failed_agent_response_without_exception():
    labels = {
        "agent": "test",
        "operation": "execute",
        "outcome": "failure",
    }

    before = metric_value(AGENT_EXECUTIONS_TOTAL, **labels)

    response = AgentResponse(
        answer="",
        status=ResponseStatus.FAILED,
        message="Document processing failed.",
    )

    result = observe_agent_execution(
        agent="test",
        operation="execute",
        call=lambda: response,
    )

    assert result is response
    assert result.status == ResponseStatus.FAILED
    assert metric_value(AGENT_EXECUTIONS_TOTAL, **labels) == before + 1