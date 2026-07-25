from app.ai.embedding_providers.base_embedding_provider import (
    BaseEmbeddingProvider,
)
from app.ai.embedding_registry import EMBEDDING_PROVIDER_REGISTRY
from app.core.config import settings
from app.core.enums import LLMProvider


class EmbeddingFactory:
    """
    Factory responsible for creating embedding providers.
    """

    @staticmethod
    def get_provider() -> BaseEmbeddingProvider:

        provider = LLMProvider(settings.LLM_PROVIDER)

        provider_class = EMBEDDING_PROVIDER_REGISTRY.get(provider)

        if provider_class is None:
            raise ValueError(f"Unsupported embedding provider: {provider}")

        return provider_class()
