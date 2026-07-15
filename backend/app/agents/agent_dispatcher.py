from app.agents.base_agent import BaseAgent
from app.agents.registry import AgentRegistry
from app.contracts.agent_request import AgentRequest
from app.contracts.agent_response import AgentResponse


_registry = AgentRegistry()


def dispatch_agent(
    agent_name: str,
    request: AgentRequest,
) -> AgentResponse:
    """
    Dispatch the request to the appropriate agent.
    """

    agent: BaseAgent = _registry.get(agent_name)

    return agent.execute(request)