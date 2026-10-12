from unittest.mock import Mock, patch

import pytest

from app.agents.agent_dispatcher import dispatch_agent
from app.agents.registry import AgentRegistry
from app.core.enums import AgentType, ResponseStatus
from app.schemas.agent_request import AgentRequest
from app.schemas.agent_response import AgentResponse


@pytest.mark.parametrize("agent_name", [AgentType.RAG, AgentType.SQL])
def test_dispatch_agent_calls_selected_agent(agent_name):
    request = AgentRequest(question="Test question")
    expected_response = AgentResponse(
        answer="Test answer",
        status=ResponseStatus.SUCCESS,
    )
    mock_agent = Mock()
    mock_agent.execute.return_value = expected_response

    with patch(
        "app.agents.agent_dispatcher._registry.get",
        return_value=mock_agent,
    ) as mock_get:
        response = dispatch_agent(agent_name, request)

    mock_get.assert_called_once_with(agent_name)
    mock_agent.execute.assert_called_once_with(request)
    assert response is expected_response


def test_registry_rejects_removed_analyst_agent():
    registry = AgentRegistry()

    with pytest.raises(ValueError, match="Unknown agent"):
        registry.get("analyst")
