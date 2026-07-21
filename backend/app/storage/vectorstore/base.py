from abc import ABC, abstractmethod
from typing import Any



class VectorProvider(ABC):
    """
    Base interface for all vector database providers.
    """

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the vector database."""
        pass

    @abstractmethod
    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: str,
    ) -> None:
        """Create a vector collection."""
        pass

    @abstractmethod
    def delete_collection(
        self,
        collection_name: str,
    ) -> None:
        """Delete a vector collection."""
        pass

    @abstractmethod
    def upsert(
        self,
        collection_name: str,
        vectors: list[dict[str, Any]],
    ) -> None:
        """Insert or update vectors."""
        pass

    @abstractmethod
    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors."""
        pass

    @abstractmethod
    def delete(
        self,
        collection_name: str,
        ids: list[str],
    ) -> None:
        """Delete vectors by ID."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the provider connection."""
        pass