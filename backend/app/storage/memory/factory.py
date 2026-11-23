from functools import lru_cache

from app.core.config import settings
from app.storage.memory.base import MemoryProvider
from app.storage.memory.providers.local_memory import LocalMemory
from app.storage.memory.providers.redis_memory import RedisMemory


@lru_cache(maxsize=1)
def get_memory_provider() -> MemoryProvider:
    provider = settings.MEMORY_PROVIDER.lower()

    if provider == "local":
        return LocalMemory(
            max_messages=settings.MEMORY_MAX_MESSAGES,
            ttl_seconds=settings.MEMORY_TTL_SECONDS,
            max_conversations=settings.MEMORY_MAX_CONVERSATIONS,
        )

    if provider == "redis":
        return RedisMemory(
            max_messages=settings.MEMORY_MAX_MESSAGES,
            ttl_seconds=settings.MEMORY_TTL_SECONDS,
        )

    raise ValueError(f"Unsupported memory provider: {provider}")