from unittest.mock import Mock

import pytest

from app.ai.embedding_factory import EmbeddingFactory
from app.ai.embedding_registry import EMBEDDING_PROVIDER_REGISTRY
from app.core.enums import LLMProvider
from app.core.config import settings


@pytest.fixture(autouse=True)
def reset_embedding_factory():
    EmbeddingFactory.reset()
    yield
    EmbeddingFactory.reset()


def test_embedding_provider_is_reused(monkeypatch):
    mock_provider = Mock()
    mock_provider_class = Mock(return_value=mock_provider)

    monkeypatch.setitem(
        EMBEDDING_PROVIDER_REGISTRY,
        LLMProvider.OPENAI,
        mock_provider_class,
    )
    monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")

    first = EmbeddingFactory.get_provider()
    second = EmbeddingFactory.get_provider()

    assert first is second
    mock_provider_class.assert_called_once()


def test_embedding_provider_changes_when_configuration_changes(
    monkeypatch,
):
    openai_provider = Mock()
    azure_provider = Mock()

    openai_class = Mock(return_value=openai_provider)
    azure_class = Mock(return_value=azure_provider)

    monkeypatch.setitem(
        EMBEDDING_PROVIDER_REGISTRY,
        LLMProvider.OPENAI,
        openai_class,
    )
    monkeypatch.setitem(
        EMBEDDING_PROVIDER_REGISTRY,
        LLMProvider.AZURE,
        azure_class,
    )

    monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")
    first = EmbeddingFactory.get_provider()

    monkeypatch.setattr(settings, "LLM_PROVIDER", "azure")
    second = EmbeddingFactory.get_provider()

    assert first is openai_provider
    assert second is azure_provider
    assert first is not second

    openai_class.assert_called_once()
    azure_class.assert_called_once()


def test_embedding_factory_reset_clears_cached_provider(monkeypatch):
    first_provider = Mock()
    second_provider = Mock()

    mock_provider_class = Mock(
        side_effect=[first_provider, second_provider]
    )

    monkeypatch.setitem(
        EMBEDDING_PROVIDER_REGISTRY,
        LLMProvider.OPENAI,
        mock_provider_class,
    )
    monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")

    first = EmbeddingFactory.get_provider()

    EmbeddingFactory.reset()

    second = EmbeddingFactory.get_provider()

    assert first is first_provider
    assert second is second_provider
    assert first is not second
    assert mock_provider_class.call_count == 2