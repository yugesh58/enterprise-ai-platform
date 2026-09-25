from app.storage.memory.factory import get_memory_provider


def main():
    memory = get_memory_provider()

    conversation_id = "test-conversation"

    memory.add_message(
        conversation_id=conversation_id,
        role="user",
        content="What AI technologies does Yugesh know?",
    )

    memory.add_message(
        conversation_id=conversation_id,
        role="assistant",
        content="Yugesh knows Generative AI, RAG, and Machine Learning.",
    )

    memory.add_message(
        conversation_id=conversation_id,
        role="user",
        content="Which of those are related to LLMs?",
    )

    history = memory.get_history(
        conversation_id=conversation_id,
    )

    print("=" * 80)
    print("CONVERSATION MEMORY TEST")
    print("=" * 80)

    for message in history:
        print(
            f"{message['role']}: "
            f"{message['content']}"
        )

    print("\n")
    print("=" * 80)
    print("CLEAR MEMORY")
    print("=" * 80)

    memory.clear(conversation_id)

    print(
        "Remaining messages:",
        memory.get_history(conversation_id),
    )


if __name__ == "__main__":
    main()