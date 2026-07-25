from app.storage.memory.conversation_memory import add_to_memory


def update_memory_node(state):
    """
    Store the successful interaction in conversation memory.
    """

    add_to_memory(
        state["question"],
        state["sql_query"],
        state["summary"],
    )

    return {}
