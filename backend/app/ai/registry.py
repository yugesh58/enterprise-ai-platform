from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.azure_provider import AzureProvider

PROVIDER_REGISTRY = {
    "openai": OpenAIProvider,
    "azure": AzureProvider,
}