from app.agents.base_agent import BaseAgent
from app.schemas.agent_request import AgentRequest
from app.schemas.agent_response import AgentResponse
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

        conversation_id = request.attributes.get(
            "conversation_id",
            "default",
        )

        graph_response = sql_graph.invoke(
            {
                "conversation_id": conversation_id,
                "question": request.question,
                "context": request.context,
                "retry_count": 0,
            }
        )

        request.context.selected_agent = AgentType.SQL

        self.logger.info("SQL Agent execution completed")

        return AgentResponse(
            answer=graph_response.get("summary", ""),
            data=graph_response,
        )
