from app.core.config import settings
from app.storage.vectorstore.providers.qdrant_provider import (
    QdrantProvider,
)


class VectorStoreFactory:

    _provider = None

    @classmethod
    def get_provider(cls):

        if cls._provider is None:

            provider_name = settings.VECTOR_DB.lower()

            if provider_name == "qdrant":

                provider = QdrantProvider()

            else:

                raise ValueError(
                    f"Unsupported vector provider: {provider_name}"
                )

            provider.connect()

            cls._provider = provider

        return cls._provider