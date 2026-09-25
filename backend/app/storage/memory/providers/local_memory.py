from collections import defaultdict

from app.storage.memory.base import MemoryProvider


class LocalMemory(MemoryProvider):
    """
    In-process conversation memory.

    Intended for local development and testing.
    """

    def __init__(
        self,
        max_messages: int = 10,
    ) -> None:
        self._max_messages = max_messages

        self._conversations: dict[
            str,
            list[dict],
        ] = defaultdict(list)

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> None:

        self._conversations[conversation_id].append(
            {
                "role": role,
                "content": content,
            }
        )

        if (
            len(self._conversations[conversation_id])
            > self._max_messages
        ):
            self._conversations[conversation_id] = (
                self._conversations[conversation_id][
                    -self._max_messages:
                ]
            )

    def get_history(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> list[dict]:

        history = self._conversations.get(
            conversation_id,
            [],
        )

        if limit <= 0:
            return []

        return history[-limit:]

    def clear(
        self,
        conversation_id: str,
    ) -> None:

        self._conversations.pop(
            conversation_id,
            None,
        )