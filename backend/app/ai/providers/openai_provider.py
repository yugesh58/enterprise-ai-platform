from typing import Any, Iterator

from langchain_openai import ChatOpenAI

from app.ai.providers.base_provider import BaseLLMProvider
from app.ai.providers.observability import (
    observe_ainvoke,
    observe_invoke,
    observe_stream,
)
from app.core.config import settings


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider with LLM-call observability."""

    def __init__(self) -> None:
        self._llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=settings.TEMPERATURE,
        )

    def get_llm(self) -> ChatOpenAI:
        return self._llm

    def invoke(self, prompt: str) -> Any:
        return observe_invoke(
            operation="invoke",
            provider="openai",
            model=settings.OPENAI_MODEL,
            call=lambda: self._llm.invoke(prompt),
        )

    async def ainvoke(self, prompt: str) -> Any:
        return await observe_ainvoke(
            operation="ainvoke",
            provider="openai",
            model=settings.OPENAI_MODEL,
            call=lambda: self._llm.ainvoke(prompt),
        )

    def stream(self, prompt: str) -> Iterator[Any]:
        chunks = self._llm.stream(prompt)
        return observe_stream(
            provider="openai",
            model=settings.OPENAI_MODEL,
            chunks=chunks,
        )
