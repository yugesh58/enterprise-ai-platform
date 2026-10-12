from unittest.mock import Mock, patch

from app.agents.rag_agent import RAGAgent
from app.core.enums import ResponseStatus
from app.schemas.agent_request import AgentRequest


@patch("app.agents.rag_agent.get_document_connection")
@patch("app.agents.rag_agent.RAGAgent._build_rag_service")
def test_rag_agent_propagates_request_and_closes_session(
    mock_build_service,
    mock_get_connection,
):
    connection = Mock()
    mock_get_connection.return_value = connection

    rag_service = Mock()
    rag_service.answer.return_value = {
        "answer": "Grounded answer",
        "sources": [
            {
                "source": "integration_test.txt",
                "page_number": 1,
            }
        ],
    }
    mock_build_service.return_value = rag_service

    agent = RAGAgent()
    request = AgentRequest(
        question="What does the document say?",
        chat_history=[{"role": "user", "content": "Earlier question"}],
        attributes={
            "document_id": "d967da93-e80a-4d94-bfff-40accb048bbd",
            "top_k": 3,
        },
    )

    response = agent.execute(request)

    assert response.status == ResponseStatus.SUCCESS
    assert response.answer == "Grounded answer"

    rag_service.answer.assert_called_once_with(
        question="What does the document say?",
        chat_history=request.chat_history,
        document_id="d967da93-e80a-4d94-bfff-40accb048bbd",
        top_k=3,
    )
    connection.close.assert_called_once()


@patch("app.agents.rag_agent.get_document_connection")
@patch("app.agents.rag_agent.RAGAgent._build_rag_service")
def test_rag_agent_closes_session_when_service_fails(
    mock_build_service,
    mock_get_connection,
):
    connection = Mock()
    mock_get_connection.return_value = connection

    rag_service = Mock()
    rag_service.answer.side_effect = RuntimeError("Simulated failure")
    mock_build_service.return_value = rag_service

    response = RAGAgent().execute(
        AgentRequest(question="Trigger a test failure")
    )

    assert response.status == ResponseStatus.FAILED
    connection.close.assert_called_once()
