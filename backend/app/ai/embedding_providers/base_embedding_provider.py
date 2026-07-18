from abc import ABC, abstractmethod
from typing import Any


class BaseEmbeddingProvider(ABC):
    """
    Base contract for embedding providers.
    """

    @abstractmethod
    def get_embeddings(self) -> Any:
        """
        Returns the embedding model instance.
        """
        raise NotImplementedError
