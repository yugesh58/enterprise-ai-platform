from langchain_openai import AzureOpenAIEmbeddings

from app.ai.embedding_providers.base_embedding_provider import (
    BaseEmbeddingProvider,
)
from app.core.config import settings


class AzureEmbeddingProvider(BaseEmbeddingProvider):
    """
    Azure OpenAI implementation of the embedding provider.
    """

    def __init__(self) -> None:
        self._embeddings = AzureOpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )

    def get_embeddings(self) -> AzureOpenAIEmbeddings:
        return self._embeddings
