from app.core.config import settings
from app.storage.vectorstore.providers.qdrant_provider import (
    QdrantProvider,
)


class VectorStoreFactory:

    _provider = None

    @classmethod
    def get_provider(cls):

        if cls._provider is None:

            provider = settings.VECTOR_DB.lower()

            if provider == "qdrant":
                cls._provider = QdrantProvider()
            else:
                raise ValueError(
                    f"Unsupported vector provider: {provider}"
                )

            cls._provider.connect()

        return cls._provider