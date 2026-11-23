
import time
from collections import OrderedDict
import threading
from app.storage.memory.base import MemoryProvider


class LocalMemory(MemoryProvider):
    """
    Bounded in-process conversation memory.

    Intended for local development and testing.
    """

    def __init__(
        self,
        max_messages: int = 10,
        ttl_seconds: int = 86400,
        max_conversations: int = 1000,

    ) -> None:
        if max_messages < 1:
            raise ValueError("max_messages must be positive.")

        if ttl_seconds < 1:
            raise ValueError("ttl_seconds must be positive.")

        if max_conversations < 1:
            raise ValueError("max_conversations must be positive.")

        self._max_messages = max_messages
        self._ttl_seconds = ttl_seconds
        self._max_conversations = max_conversations
        self._lock = threading.RLock()

        # OrderedDict maintains least-recently-used ordering.
        # Each entry contains messages and its last activity timestamp.
        self._conversations: OrderedDict[
            str,
            tuple[list[dict], float],
        ] = OrderedDict()

    @staticmethod
    def _validate_conversation_id(conversation_id: str) -> None:
        if (
            not isinstance(conversation_id, str)
            or not conversation_id
            or len(conversation_id) > 128
        ):
            raise ValueError("Invalid conversation_id.")

    @staticmethod
    def _validate_message(role: str, content: str) -> None:
        if not isinstance(role, str) or role not in {
            "user",
            "assistant",
            "system",
        }:
            raise ValueError("Invalid conversation message role.")

        if not isinstance(content, str):
            raise ValueError("Message content must be a string.")

    def _remove_expired(self, now: float) -> None:
        expired_ids = [
            conversation_id
            for conversation_id, (_, last_activity)
            in self._conversations.items()
            if now - last_activity >= self._ttl_seconds
        ]

        for conversation_id in expired_ids:
            self._conversations.pop(conversation_id, None)

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> None:
        self._validate_conversation_id(conversation_id)
        self._validate_message(role, content)

        now = time.monotonic()
        self._remove_expired(now)

        if conversation_id in self._conversations:
            messages, _ = self._conversations[conversation_id]
        else:
            if len(self._conversations) >= self._max_conversations:
                self._conversations.popitem(last=False)

            messages = []

        messages.append({
            "role": role,
            "content": content,
        })

        messages = messages[-self._max_messages:]

        self._conversations[conversation_id] = (messages, now)
        self._conversations.move_to_end(conversation_id)

    def get_history(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> list[dict]:
        self._validate_conversation_id(conversation_id)

        if limit <= 0:
            return []

        now = time.monotonic()
        self._remove_expired(now)

        entry = self._conversations.get(conversation_id)

        if entry is None:
            return []

        messages, _ = entry

        # Refresh inactivity TTL on successful access.
        self._conversations[conversation_id] = (messages, now)
        self._conversations.move_to_end(conversation_id)

        return messages[-min(limit, self._max_messages):]

    def clear(
        self,
        conversation_id: str,
    ) -> None:
        self._validate_conversation_id(conversation_id)
        self._conversations.pop(conversation_id, None)
