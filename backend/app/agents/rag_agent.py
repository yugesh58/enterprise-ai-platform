from app.agents.base_agent import BaseAgent
from app.contracts.agent_request import AgentRequest
from app.contracts.agent_response import AgentResponse
from app.core.enums import AgentType

from app.storage.vectorstore.faiss_manager import (
    load_vectorstore,
    retrieve_chunk,
)

from app.services.rag_service import generate_rag_answer


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

        vectorstore = load_vectorstore()

        documents = retrieve_chunk(
            vectorstore,
            request.question,
        )

        answer = generate_rag_answer(
            documents,
            request.question,
        )

        request.context.selected_agent = AgentType.RAG

        self.logger.info("RAG Agent execution completed")

        return AgentResponse(
            answer=answer,
            data={
                "documents": documents,
            },
        )