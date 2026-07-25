from abc import ABC, abstractmethod
from typing import Optional

from app.storage.vectorstore.models.vector_point import VectorPoint


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
        distance: str = "COSINE",
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
        points: list[VectorPoint],
    ) -> None:
        """Insert or update vector points."""
        pass

    @abstractmethod
    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """Search similar vectors."""
        pass

    @abstractmethod
    def delete(
        self,
        collection_name: str,
        point_ids: list[str],
    ) -> None:
        """Delete vectors."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the provider connection."""
        pass