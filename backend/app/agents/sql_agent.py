import time

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

        start_time = time.perf_counter()

        graph_response = sql_graph.invoke(
            {
                "conversation_id": conversation_id,
                "question": request.question,
                "context": request.context,
                "retry_count": 0,
            }
        )

        total_latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        # Store total end-to-end latency.
        graph_response["total_latency_ms"] = total_latency_ms

        request.context.selected_agent = AgentType.SQL

        self.logger.info(
            "SQL Agent execution completed | "
            "total_latency_ms=%.2f",
            total_latency_ms,
        )

        return AgentResponse(
            answer=graph_response.get("summary", ""),
            data=graph_response,
        )