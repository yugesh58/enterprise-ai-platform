from app.agents.base_agent import BaseAgent
from app.contracts.agent_request import AgentRequest
from app.contracts.agent_response import AgentResponse

from app.graphs.sql_graph import sql_graph


class SQLAgent(BaseAgent):

    def execute(
        self,
        request: AgentRequest
    ) -> AgentResponse:

        self.logger.info("Executing SQL Agent")

        graph_response = sql_graph.invoke(
            {
                "question": request.question,
                "retry_count": 0
            }
        )

        request.context.selected_agent = "sql"

        return AgentResponse(
            answer=graph_response.get("answer", ""),
            data=graph_response
        )