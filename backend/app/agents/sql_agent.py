from app.agents.base_agent import BaseAgent
from app.contracts.agent_request import AgentRequest
from app.contracts.agent_response import AgentResponse
from app.core.enums import AgentType

from app.workflows.sql.graph import sql_graph


class SQLAgent(BaseAgent):
    """
    Agent responsible for answering structured
    data queries.
    """

    def execute(
        self,
        request: AgentRequest,
    ) -> AgentResponse:

        self.logger.info("Executing SQL Agent")

        graph_response = sql_graph.invoke(
            {
                "question": request.question,
                "context": request.context,
                "retry_count": 0,
            }
        )

        request.context.selected_agent = AgentType.SQL

        self.logger.info("SQL Agent execution completed")

        return AgentResponse(
            answer=graph_response.get("answer", ""),
            data=graph_response,
        )