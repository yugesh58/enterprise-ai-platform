
import hashlib
import json

from app.storage.memory.base import MemoryProvider
from app.storage.redis_client import get_redis_client


class RedisMemory(MemoryProvider):
    """
    Redis-backed conversation memory.

    Stores bounded conversation histories with automatic expiration.
    """

    def __init__(
        self,
        max_messages: int = 10,
        ttl_seconds: int = 86400,
        key_prefix: str = "enterprise-ai:conversation:",
    ) -> None:
        if max_messages < 1:
            raise ValueError("max_messages must be positive.")

        if ttl_seconds < 1:
            raise ValueError("ttl_seconds must be positive.")

        if not isinstance(key_prefix, str) or not key_prefix:
            raise ValueError("key_prefix must be a non-empty string.")

        self._max_messages = max_messages
        self._ttl_seconds = ttl_seconds
        self._key_prefix = key_prefix

    def _get_key(self, conversation_id: str) -> str:
        if not isinstance(conversation_id, str):
            raise ValueError("conversation_id must be a string.")

        if not conversation_id or len(conversation_id) > 128:
            raise ValueError("Invalid conversation_id.")

        digest = hashlib.sha256(
            conversation_id.encode("utf-8")
        ).hexdigest()

        return f"{self._key_prefix}{digest}"

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> None:
        if not isinstance(role, str) or role not in {
            "user",
            "assistant",
            "system",
        }:
            raise ValueError("Invalid conversation message role.")

        if not isinstance(content, str):
            raise ValueError("Message content must be a string.")

        key = self._get_key(conversation_id)

        message = json.dumps(
            {
                "role": role,
                "content": content,
            },
            ensure_ascii=False,
        )

        client = get_redis_client()

        # Execute all list updates and expiration atomically.
        with client.pipeline(transaction=True) as pipeline:
            pipeline.rpush(key, message)
            pipeline.ltrim(key, -self._max_messages, -1)
            pipeline.expire(key, self._ttl_seconds)
            pipeline.execute()

    def get_history(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> list[dict]:
        key = self._get_key(conversation_id)

        if limit <= 0:
            return []

        client = get_redis_client()

        messages = client.lrange(
            key,
            -min(limit, self._max_messages),
            -1,
        )

        # Refresh TTL when an existing conversation is accessed.
        if messages:
            client.expire(key, self._ttl_seconds)

        return [
            json.loads(message)
            for message in messages
        ]

    def clear(
        self,
        conversation_id: str,
    ) -> None:
        key = self._get_key(conversation_id)
        get_redis_client().delete(key)
