from typing import Type

from app.ai.embedding_providers.base_embedding_provider import (
    BaseEmbeddingProvider,
)
from app.ai.embedding_providers.openai_embedding_provider import (
    OpenAIEmbeddingProvider,
)
from app.ai.embedding_providers.azure_embedding_provider import (
    AzureEmbeddingProvider,
)
from app.core.enums import LLMProvider


EMBEDDING_PROVIDER_REGISTRY: dict[
    LLMProvider,
    Type[BaseEmbeddingProvider],
] = {
    LLMProvider.OPENAI: OpenAIEmbeddingProvider,
    LLMProvider.AZURE: AzureEmbeddingProvider,
}