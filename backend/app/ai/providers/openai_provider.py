from langchain_openai import ChatOpenAI

from app.ai.providers.base_provider import BaseLLMProvider
from app.core.config import settings


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI implementation of the BaseLLMProvider.
    """

    def __init__(self):
        self._llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=settings.TEMPERATURE,
        )

    def get_llm(self):
        return self._llm

    def invoke(self, prompt: str):
        return self._llm.invoke(prompt)

    def stream(self, prompt: str):
        return self._llm.stream(prompt)