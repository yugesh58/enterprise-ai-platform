"""
Application-wide lazy LLM provider.

All workflows and services should import `provider`
from this module instead of instantiating providers
directly.
"""

from threading import Lock
from typing import Any, Iterator

from app.ai.llm_factory import LLMFactory
from app.ai.providers.base_provider import BaseLLMProvider


class LazyLLMProvider(BaseLLMProvider):
    """Thread-safe provider proxy initialized on first use."""

    def __init__(self) -> None:
        self._provider: BaseLLMProvider | None = None
        self._lock = Lock()

    def _get_provider(self) -> BaseLLMProvider:
        if self._provider is None:
            with self._lock:
                if self._provider is None:
                    self._provider = LLMFactory.get_provider()

        return self._provider

    def get_llm(self) -> Any:
        return self._get_provider().get_llm()

    def invoke(self, prompt: str) -> Any:
        return self._get_provider().invoke(prompt)

    async def ainvoke(self, prompt: str) -> Any:
        return await self._get_provider().ainvoke(prompt)

    def stream(self, prompt: str) -> Iterator[Any]:
        return self._get_provider().stream(prompt)


provider = LazyLLMProvider()
