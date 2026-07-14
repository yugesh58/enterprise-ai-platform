from enum import StrEnum


class AgentType(StrEnum):
    """
    Supported AI agents.
    """

    SQL = "sql"
    RAG = "rag"
    ANALYST = "analyst"


class ResponseStatus(StrEnum):
    """
    Standard API response status.
    """

    SUCCESS = "success"
    FAILED = "failed"