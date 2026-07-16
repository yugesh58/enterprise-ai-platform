from app.ai.providers.base_provider import BaseLLMProvider
from app.ai.llm_registry import LLM_PROVIDER_REGISTRY
from app.core.config import settings
from app.core.enums import LLMProvider


class LLMFactory:
    """
    Factory responsible for creating LLM provider instances.
    """

    @staticmethod
    def get_provider() -> BaseLLMProvider:

        provider = LLMProvider(settings.LLM_PROVIDER)

        provider_class = LLM_PROVIDER_REGISTRY.get(provider)

        if provider_class is None:
            raise ValueError(
                f"Unsupported LLM provider: {provider}"
            )

        return provider_class()