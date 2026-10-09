
from typing import Dict

from app.agents.base_agent import BaseAgent
from app.agents.rag_agent import RAGAgent
from app.agents.sql_agent import SQLAgent
from app.core.enums import AgentType


class AgentRegistry:
    """
    Registry responsible for managing available agents.

    Agents are initialized on first use, avoiding external
    service connections during API module import.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}

    def get(self, name: str) -> BaseAgent:
        """Return the requested agent, creating it when needed."""

        if name not in {AgentType.SQL, AgentType.RAG}:
            raise ValueError(f"Unknown agent: {name}")

        if name not in self._agents:
            if name == AgentType.SQL:
                self._agents[name] = SQLAgent()
            else:
                self._agents[name] = RAGAgent()

        return self._agents[name]
