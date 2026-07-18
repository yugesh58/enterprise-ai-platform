from app.agents.base_agent import BaseAgent
from app.contracts.agent_request import AgentRequest
from app.contracts.agent_response import AgentResponse
from app.core.enums import AgentType
from app.workflows.analyst.graph import analyst_graph


class AnalystAgent(BaseAgent):
    def execute(
        self,
        request: AgentRequest,
    ) -> AgentResponse:

        self.logger.info("Executing Analyst Agent")

        graph_response = analyst_graph.invoke(
            {
                "question": request.question,
            }
        )

        request.context.selected_agent = AgentType.ANALYST

        self.logger.info("Analyst Agent execution completed")

        return AgentResponse(
            answer=graph_response["summary"],
            chart=graph_response.get("chart_path"),
        )
