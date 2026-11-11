
from app.ai.embedding_providers.base_embedding_provider import (
    BaseEmbeddingProvider,
)
from app.ai.embedding_registry import EMBEDDING_PROVIDER_REGISTRY
from app.core.config import settings
from app.core.enums import LLMProvider


class EmbeddingFactory:
    """
    Factory responsible for creating and reusing embedding providers.
    """

    _provider: BaseEmbeddingProvider | None = None
    _provider_name: LLMProvider | None = None

    @classmethod
    def get_provider(cls) -> BaseEmbeddingProvider:
        provider_name = LLMProvider(settings.LLM_PROVIDER)

        if cls._provider is not None and cls._provider_name == provider_name:
            return cls._provider

        provider_class = EMBEDDING_PROVIDER_REGISTRY.get(provider_name)

        if provider_class is None:
            raise ValueError(
                f"Unsupported embedding provider: {provider_name}"
            )

        provider = provider_class()

        cls._provider = provider
        cls._provider_name = provider_name

        return provider

    @classmethod
    def reset(cls) -> None:
        """Reset the cached provider instance."""
        cls._provider = None
        cls._provider_name = None
