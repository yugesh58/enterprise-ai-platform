from typing import Any, Iterator

from langchain_openai import ChatOpenAI

from app.ai.providers.base_provider import BaseLLMProvider
from app.core.config import settings


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI implementation of the BaseLLMProvider.
    """

    def __init__(self) -> None:
        self._llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=settings.TEMPERATURE,
        )

    def get_llm(self) -> ChatOpenAI:
        """
        Returns the configured ChatOpenAI instance.
        """
        return self._llm

    def invoke(self, prompt: str) -> Any:
        """
        Invoke the model synchronously.
        """
        return self._llm.invoke(prompt)

    async def ainvoke(self, prompt: str) -> Any:
        """
        Invoke the model asynchronously.
        """
        return await self._llm.ainvoke(prompt)

    def stream(self, prompt: str) -> Iterator[Any]:
        """
        Stream the model response.
        """
        return self._llm.stream(prompt)