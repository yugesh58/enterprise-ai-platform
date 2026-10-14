
import time

from app.agents.base_agent import BaseAgent
from app.schemas.agent_request import AgentRequest
from app.schemas.agent_response import AgentResponse
from app.core.enums import AgentType
from app.workflows.sql.graph import sql_graph


class SQLAgent(BaseAgent):
    """Agent responsible for answering structured data queries."""

    def execute(self, request: AgentRequest) -> AgentResponse:
        start_time = time.perf_counter()

        conversation_id = request.attributes.get(
            "conversation_id",
            "default",
        )

        self.logger.info("SQL Agent execution started")

        try:
            graph_response = sql_graph.invoke(
                {
                    "conversation_id": conversation_id,
                    "question": request.question,
                    "context": request.context,
                    "retry_count": 0,
                }
            )

            total_latency_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )

            graph_response["total_latency_ms"] = total_latency_ms
            request.context.selected_agent = AgentType.SQL

            self.logger.info(
                "SQL Agent execution completed",
                extra={
                    "agent": str(AgentType.SQL),
                    "duration_ms": total_latency_ms,
                    "outcome": "success",
                },
            )

            return AgentResponse(
                answer=graph_response.get("summary", ""),
                data=graph_response,
            )

        except Exception:
            total_latency_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )

            self.logger.exception(
                "SQL Agent execution failed",
                extra={
                    "agent": str(AgentType.SQL),
                    "duration_ms": total_latency_ms,
                    "outcome": "failure",
                },
            )
            raise
