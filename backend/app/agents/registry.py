from typing import Dict

from app.agents.base_agent import BaseAgent
from app.agents.sql_agent import SQLAgent
from app.agents.rag_agent import RAGAgent
from app.agents.analyst_agent import AnalystAgent

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {
        "sql": SQLAgent(),
        "rag": RAGAgent(),
        "analyst": AnalystAgent()
    }
        
    def get(self, name: str) -> BaseAgent:

        if name not in self._agents:
            raise ValueError(f"Unknown agent: {name}")

        return self._agents[name]