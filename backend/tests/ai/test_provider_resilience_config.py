from unittest.mock import patch

from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.azure_provider import AzureProvider
from app.core.config import settings


def test_openai_provider_uses_configured_timeout_and_retries():
    with (
        patch("app.ai.providers.openai_provider.ChatOpenAI") as mock_client,
        patch.object(settings, "LLM_TIMEOUT_SECONDS", 15.0),
        patch.object(settings, "LLM_MAX_RETRIES", 3),
    ):
        OpenAIProvider()

    mock_client.assert_called_once()
    kwargs = mock_client.call_args.kwargs

    assert kwargs["timeout"] == 15.0
    assert kwargs["max_retries"] == 3


def test_azure_provider_uses_configured_timeout_and_retries():
    with (
        patch("app.ai.providers.azure_provider.AzureChatOpenAI") as mock_client,
        patch.object(settings, "LLM_TIMEOUT_SECONDS", 20.0),
        patch.object(settings, "LLM_MAX_RETRIES", 4),
    ):
        AzureProvider()

    mock_client.assert_called_once()
    kwargs = mock_client.call_args.kwargs

    assert kwargs["timeout"] == 20.0
    assert kwargs["max_retries"] == 4