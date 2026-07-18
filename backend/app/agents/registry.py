from typing import Dict

from app.agents.analyst_agent import AnalystAgent
from app.agents.base_agent import BaseAgent
from app.agents.rag_agent import RAGAgent
from app.agents.sql_agent import SQLAgent
from app.core.enums import AgentType


class AgentRegistry:
    """
    Registry responsible for managing all available agents.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {
            AgentType.SQL: SQLAgent(),
            AgentType.RAG: RAGAgent(),
            AgentType.ANALYST: AnalystAgent(),
        }

    def get(self, name: str) -> BaseAgent:
        """
        Returns the requested agent instance.
        """

        if name not in self._agents:
            raise ValueError(f"Unknown agent: {name}")

        return self._agents[name]
