from app.storage.memory.factory import get_memory_provider


def update_memory_node(state):
    """
    Store the successful interaction in conversation memory.
    """

    memory_provider = get_memory_provider()

    conversation_id = state["conversation_id"]

    memory_provider.add_message(
        conversation_id,
        "user",
        state["question"],
    )

    memory_provider.add_message(
        conversation_id,
        "assistant",
        state["summary"],
    )

    return {}
