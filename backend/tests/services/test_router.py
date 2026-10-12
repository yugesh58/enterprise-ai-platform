from unittest.mock import Mock, patch

import pytest

from app.core.enums import AgentType
from app.services.router import route_question


@pytest.mark.parametrize(
    ("question", "expected_agent"),
    [
        ("Show all employees", AgentType.SQL),
        ("What does the leave policy say?", AgentType.RAG),
    ],
)
def test_route_question_returns_valid_agent(question, expected_agent):
    with patch("app.services.router.provider.invoke") as mock_invoke:
        mock_invoke.return_value = Mock(
            content=expected_agent.value,
        )

        result = route_question(question)

    assert result == expected_agent.value


def test_route_question_rejects_empty_question():
    with pytest.raises(ValueError, match="Question cannot be empty"):
        route_question("   ")


def test_route_question_rejects_invalid_provider_response():
    with patch("app.services.router.provider.invoke") as mock_invoke:
        mock_invoke.return_value = Mock(content="analyst")

        with pytest.raises(ValueError, match="Invalid router response"):
            route_question("Which region has highest profit?")
