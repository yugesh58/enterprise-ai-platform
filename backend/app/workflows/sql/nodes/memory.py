from app.storage.memory.conversation_memory import get_memory


def retrieve_memory_node(state):
    """
    Retrieve conversation memory.
    """

    memory = get_memory()

    return {"memory": memory}
