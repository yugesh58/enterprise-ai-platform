from app.agents.registry import AgentRegistry
from app.contracts.agent_request import AgentRequest


_registry = AgentRegistry()


def dispatch_agent(
    agent_name: str,
    request: AgentRequest,
):
    """
    Dispatches the request to the correct agent.
    """

    agent = _registry.get(agent_name)

    return agent.execute(request)