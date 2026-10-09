from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.agent_response import AgentResponse

client = TestClient(app)


@patch("app.api.chat.dispatch_agent")
@patch("app.api.chat.route_question", return_value="sql")
def test_chat_passes_conversation_id_to_agent(
    mock_router,
    mock_dispatch,
):
    mock_dispatch.return_value = AgentResponse(
        answer="There are 5 employees.",
    )

    response = client.post(
        "/chat",
        json={
            "question": "How many employees are there?",
            "conversation_id": "conversation-123",
        },
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"] == "conversation-123"

    agent_request = mock_dispatch.call_args.args[1]

    assert agent_request.attributes["conversation_id"] == "conversation-123"
    assert agent_request.context.conversation_id == "conversation-123"
    assert agent_request.context.selected_agent == "sql"


@patch("app.api.chat.dispatch_agent")
@patch("app.api.chat.route_question", return_value="rag")
def test_chat_generates_conversation_id_when_missing(
    mock_router,
    mock_dispatch,
):
    mock_dispatch.return_value = AgentResponse(
        answer="Found three relevant documents.",
    )

    response = client.post(
        "/chat",
        json={"question": "Summarize the documents"},
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"]


def test_chat_rejects_empty_question():
    response = client.post(
        "/chat",
        json={"question": "   "},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["message"] == "Question cannot be empty."