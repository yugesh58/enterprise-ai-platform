from app.ai.providers.base_provider import BaseLLMProvider


class AzureProvider(BaseLLMProvider):
    """
    Placeholder Azure provider.

    This will be implemented when we migrate from OpenAI
    to Azure OpenAI.
    """

    def __init__(self):
        raise NotImplementedError(
            "Azure Provider is not implemented yet."
        )

    def get_llm(self):
        raise NotImplementedError

    def invoke(self, prompt: str):
        raise NotImplementedError

    def stream(self, prompt: str):
        raise NotImplementedError