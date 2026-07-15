from abc import ABC, abstractmethod
from typing import Any, Iterator


class BaseLLMProvider(ABC):
    """
    Base contract for every LLM provider.

    Implementations include:
    - OpenAI
    - Azure OpenAI
    - Anthropic
    - Ollama
    """

    @abstractmethod
    def get_llm(self) -> Any:
        """
        Returns the underlying LangChain LLM instance.
        """
        raise NotImplementedError

    @abstractmethod
    def invoke(self, prompt: str) -> Any:
        """
        Sends a prompt to the model and returns the response.
        """
        raise NotImplementedError

    @abstractmethod
    async def ainvoke(self, prompt: str) -> Any:
        """
        Asynchronously invokes the model.
        """
        raise NotImplementedError

    @abstractmethod
    def stream(self, prompt: str) -> Iterator[Any]:
        """
        Streams the response from the model.
        """
        raise NotImplementedError