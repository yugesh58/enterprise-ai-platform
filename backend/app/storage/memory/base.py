from abc import ABC, abstractmethod


class MemoryProvider(ABC):
    """
    Abstract interface for conversation memory.

    Memory providers store conversational turns independently
    of the agent using them.
    """

    @abstractmethod
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> None:
        """
        Store a single conversation message.
        """
        raise NotImplementedError

    @abstractmethod
    def get_history(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        Retrieve recent conversation history.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(
        self,
        conversation_id: str,
    ) -> None:
        """
        Clear conversation history.
        """
        raise NotImplementedError