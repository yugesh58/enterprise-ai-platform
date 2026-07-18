from enum import StrEnum


class AgentType(StrEnum):
    """
    Supported AI agents.
    """

    SQL = "sql"
    RAG = "rag"
    ANALYST = "analyst"


class LLMProvider(StrEnum):
    OPENAI = "openai"
    AZURE = "azure"


class ResponseStatus(StrEnum):
    """
    Standard API response status.
    """

    SUCCESS = "success"
    FAILED = "failed"


class ValidationStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
