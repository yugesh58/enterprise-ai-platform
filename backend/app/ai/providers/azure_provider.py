from typing import Any, Iterator

from langchain_openai import AzureChatOpenAI

from app.ai.providers.base_provider import BaseLLMProvider
from app.ai.providers.observability import (
    observe_ainvoke,
    observe_invoke,
    observe_stream,
)
from app.core.config import settings


class AzureProvider(BaseLLMProvider):
    """
    Azure OpenAI implementation of the BaseLLMProvider
    with LLM-call observability.
    """

    def __init__(self) -> None:
        self._llm = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
            temperature=settings.TEMPERATURE,
            api_version="2024-02-01",
        )

    def get_llm(self) -> AzureChatOpenAI:
        return self._llm

    def invoke(self, prompt: str) -> Any:
        return observe_invoke(
            operation="invoke",
            provider="azure",
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            call=lambda: self._llm.invoke(prompt),
        )

    async def ainvoke(self, prompt: str) -> Any:
        return await observe_ainvoke(
            operation="ainvoke",
            provider="azure",
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            call=lambda: self._llm.ainvoke(prompt),
        )

    def stream(self, prompt: str) -> Iterator[Any]:
        chunks = self._llm.stream(prompt)
        return observe_stream(
            provider="azure",
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            chunks=chunks,
        )
