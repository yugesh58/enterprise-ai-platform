from abc import ABC, abstractmethod

from app.contracts.agent_request import AgentRequest
from app.contracts.agent_response import AgentResponse
from app.core.logging import get_logger


class BaseAgent(ABC):
    """
    Base contract for all AI agents.

    Every agent receives an AgentRequest and returns
    an AgentResponse.
    """

    def __init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def execute(
        self,
        request: AgentRequest,
    ) -> AgentResponse:
        """
        Execute the agent.
        """
        raise NotImplementedError