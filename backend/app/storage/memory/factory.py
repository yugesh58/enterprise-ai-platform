from app.storage.memory.base import MemoryProvider
from app.storage.memory.providers.local_memory import LocalMemory


_memory_provider = LocalMemory()


def get_memory_provider() -> MemoryProvider:
    """
    Return the shared conversation memory provider.

    LocalMemory is currently used for development.
    Redis can replace this later without changing
    agent-level memory usage.
    """
    return _memory_provider