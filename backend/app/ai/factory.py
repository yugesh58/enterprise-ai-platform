from app.ai.registry import PROVIDER_REGISTRY
from app.core.config import settings


class LLMFactory:
    """
    Factory responsible for creating LLM providers.
    """

    @staticmethod
    def get_provider():

        provider_name = settings.LLM_PROVIDER.lower()

        provider_class = PROVIDER_REGISTRY.get(provider_name)

        if provider_class is None:
            raise ValueError(
                f"Unsupported LLM provider: {provider_name}"
            )

        return provider_class()