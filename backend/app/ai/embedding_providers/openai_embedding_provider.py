from langchain_openai import OpenAIEmbeddings

from app.ai.embedding_providers.base_embedding_provider import (
    BaseEmbeddingProvider,
)
from app.core.config import settings


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI implementation of the embedding provider.
    """

    def __init__(self) -> None:
        self._embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )

    def get_embeddings(self) -> OpenAIEmbeddings:
        return self._embeddings
