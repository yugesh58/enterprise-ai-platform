from abc import ABC, abstractmethod
from typing import Any


class BaseLLMProvider(ABC):
    """
    Base contract for every LLM provider.

    Any provider (OpenAI, Azure OpenAI, Anthropic, Ollama)
    must implement these methods.
    """

    @abstractmethod
    def get_llm(self) -> Any:
        """
        Return the initialized LangChain LLM instance.
        """
        pass

    @abstractmethod
    def invoke(self, prompt: str) -> str:
        """
        Invoke the model with a prompt and return the response.
        """
        pass

    @abstractmethod
    def stream(self, prompt: str):
        """
        Stream the model response.
        """
        pass