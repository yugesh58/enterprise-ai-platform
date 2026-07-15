from typing import Type

from app.ai.providers.base_provider import BaseLLMProvider
from app.ai.providers.azure_provider import AzureProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.enums import LLMProvider


LLM_PROVIDER_REGISTRY: dict[
    LLMProvider,
    Type[BaseLLMProvider],
] = {
    LLMProvider.OPENAI: OpenAIProvider,
    LLMProvider.AZURE: AzureProvider,
}