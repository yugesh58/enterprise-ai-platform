from app.agents.base_agent import BaseAgent
from app.contracts.agent_request import AgentRequest
from app.contracts.agent_response import AgentResponse

from app.storage.vectorstore.faiss_manager import (
    load_vectorstore,
    retrieve_chunk,
)

from app.services.rag_service import generate_rag_answer


class RAGAgent(BaseAgent):

    def execute(
        self,
        request: AgentRequest
    ) -> AgentResponse:

        self.logger.info("Executing RAG Agent")

        vectorstore = load_vectorstore()

        docs = retrieve_chunk(
            vectorstore,
            request.question
        )

        answer = generate_rag_answer(
            docs,
            request.question
        )

        request.context.selected_agent = "rag"

        return AgentResponse(
            answer=answer,
            data={
                "documents": docs
            }
        )