
import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def parse_sse_events(body: str) -> list[tuple[str, dict]]:
    events = []
    current_event = None

    for line in body.splitlines():
        if line.startswith("event: "):
            current_event = line.removeprefix("event: ")

        elif line.startswith("data: ") and current_event:
            payload = json.loads(line.removeprefix("data: "))
            events.append((current_event, payload))
            current_event = None

    return events


@patch("app.api.chat.RAGAgent")
@patch("app.api.chat.route_question", return_value="rag")
def test_stream_returns_sse_chunks_and_conversation_headers(
    mock_router,
    mock_rag_agent,
):
    mock_rag_agent.return_value.stream.return_value = iter(
        ["Hello ", "from ", "RAG."]
    )

    response = client.post(
        "/chat/stream",
        json={
            "question": "Summarize my documents",
            "conversation_id": "stream-test-123",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/event-stream"
    )
    assert response.headers["X-Conversation-ID"] == "stream-test-123"
    assert response.headers["X-Agent"] == "rag"

    events = parse_sse_events(response.text)

    chunks = [
        payload["chunk"]
        for event, payload in events
        if event == "chunk"
    ]

    assert chunks == ["Hello ", "from ", "RAG."]
    assert events[-1] == (
        "done",
        {"conversation_id": "stream-test-123"},
    )

    agent_request = (
        mock_rag_agent.return_value.stream.call_args.args[0]
    )

    assert agent_request.context.conversation_id == "stream-test-123"
    assert agent_request.context.selected_agent == "rag"
    assert agent_request.attributes["conversation_id"] == "stream-test-123"


@patch("app.api.chat.route_question", return_value="sql")
def test_sql_stream_returns_supported_message(mock_router):
    response = client.post(
        "/chat/stream",
        json={
            "question": "How many employees are there?",
            "conversation_id": "sql-stream-test",
        },
    )

    assert response.status_code == 200

    events = parse_sse_events(response.text)

    assert any(
        event == "message"
        and "Streaming is currently supported"
        in payload["message"]
        for event, payload in events
    )

    assert events[-1][0] == "done"


@patch("app.api.chat.RAGAgent")
@patch("app.api.chat.route_question", return_value="rag")
def test_stream_returns_safe_error_event(
    mock_router,
    mock_rag_agent,
):
    def failing_stream(_request):
        yield "Partial response "
        raise RuntimeError("internal database credentials")

    mock_rag_agent.return_value.stream.side_effect = failing_stream

    response = client.post(
        "/chat/stream",
        json={"question": "Summarize my documents"},
    )

    events = parse_sse_events(response.text)

    assert any(event == "chunk" for event, _ in events)

    assert events[-1] == (
        "error",
        {
            "message": (
                "An error occurred while streaming the response."
            )
        },
    )

    assert "internal database credentials" not in response.text


def test_stream_rejects_empty_question():
    response = client.post(
        "/chat/stream",
        json={"question": "   "},
    )

    assert response.status_code == 400

    events = parse_sse_events(response.text)

    assert events[0] == (
        "error",
        {"message": "Question cannot be empty."},
    )
