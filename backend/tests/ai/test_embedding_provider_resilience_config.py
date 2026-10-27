from unittest.mock import patch

from app.ai.embedding_providers.openai_embedding_provider import (
    OpenAIEmbeddingProvider,
)
from app.ai.embedding_providers.azure_embedding_provider import (
    AzureEmbeddingProvider,
)
from app.core.config import settings


def test_openai_embeddings_use_configured_timeout_and_retries():
    with (
        patch(
            "app.ai.embedding_providers.openai_embedding_provider.OpenAIEmbeddings"
        ) as mock_client,
        patch.object(settings, "EMBEDDING_TIMEOUT_SECONDS", 12.0),
        patch.object(settings, "EMBEDDING_MAX_RETRIES", 3),
    ):
        OpenAIEmbeddingProvider()

    kwargs = mock_client.call_args.kwargs
    assert kwargs["timeout"] == 12.0
    assert kwargs["max_retries"] == 3


def test_azure_embeddings_use_configured_timeout_and_retries():
    with (
        patch(
            "app.ai.embedding_providers.azure_embedding_provider.AzureOpenAIEmbeddings"
        ) as mock_client,
        patch.object(settings, "EMBEDDING_TIMEOUT_SECONDS", 18.0),
        patch.object(settings, "EMBEDDING_MAX_RETRIES", 4),
    ):
        AzureEmbeddingProvider()

    kwargs = mock_client.call_args.kwargs
    assert kwargs["timeout"] == 18.0
    assert kwargs["max_retries"] == 4