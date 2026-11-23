from unittest.mock import MagicMock, patch

from app.workflows.sql.nodes.update_memory import update_memory_node


def test_api_managed_memory_skips_sql_workflow_writes():
    state = {
        "conversation_id": "api-conversation",
        "memory_managed_by_api": True,
        "question": "How many employees are there?",
        "summary": "There are 5 employees.",
    }

    with patch(
        "app.workflows.sql.nodes.update_memory.get_memory_provider"
    ) as mock_get_provider:
        result = update_memory_node(state)

    mock_get_provider.assert_not_called()
    assert result == {}


def test_direct_sql_agent_writes_user_and_assistant_messages():
    state = {
        "conversation_id": "direct-conversation",
        "memory_managed_by_api": False,
        "question": "How many employees are there?",
        "summary": "There are 5 employees.",
    }

    mock_memory = MagicMock()

    with patch(
        "app.workflows.sql.nodes.update_memory.get_memory_provider",
        return_value=mock_memory,
    ):
        result = update_memory_node(state)

    assert result == {}
    assert mock_memory.add_message.call_count == 2

    calls = mock_memory.add_message.call_args_list

    assert calls[0].args == (
        "direct-conversation",
        "user",
        "How many employees are there?",
    )
    assert calls[1].args == (
        "direct-conversation",
        "assistant",
        "There are 5 employees.",
    )


def test_missing_ownership_flag_preserves_direct_agent_behaviour():
    state = {
        "conversation_id": "legacy-conversation",
        "question": "How many employees are there?",
        "summary": "There are 5 employees.",
    }

    mock_memory = MagicMock()

    with patch(
        "app.workflows.sql.nodes.update_memory.get_memory_provider",
        return_value=mock_memory,
    ):
        update_memory_node(state)

    assert mock_memory.add_message.call_count == 2