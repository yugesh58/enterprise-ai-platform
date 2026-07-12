from abc import ABC, abstractmethod

from app.contracts.agent_request import AgentRequest
from app.contracts.agent_response import AgentResponse
from app.core.logging import get_logger


class BaseAgent(ABC):

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def execute(
        self,
        request: AgentRequest
    ) -> AgentResponse:
        pass