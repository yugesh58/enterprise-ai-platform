from app.storage.memory.factory import get_memory_provider


def retrieve_memory_node(state):
    """
    Retrieve conversation history for the current conversation.
    """

    memory_provider = get_memory_provider()

    conversation_id = state["conversation_id"]

    memory = memory_provider.get_history(
        conversation_id=conversation_id,
        limit=10,
    )

    return {
        "memory": memory,
    }
