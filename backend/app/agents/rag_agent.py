from app.agents.base_agent import BaseAgent
from app.contracts.agent_request import AgentRequest
from app.contracts.agent_response import AgentResponse
from app.core.enums import AgentType

from app.workflows.rag.graph import rag_graph


class RAGAgent(BaseAgent):
    """
    Agent responsible for answering questions using
    retrieval-augmented generation (RAG).
    """

    def execute(
        self,
        request: AgentRequest,
    ) -> AgentResponse:

        self.logger.info("Executing RAG Agent")

        graph_response = rag_graph.invoke(
            {
                "question": request.question,
            }
        )

        request.context.selected_agent = AgentType.RAG

        self.logger.info("RAG Agent execution completed")

        return AgentResponse(
            answer=graph_response["answer"],
            data=graph_response,
        )