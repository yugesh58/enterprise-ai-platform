from collections.abc import Iterator

from app.agents.base_agent import BaseAgent
from app.core.enums import AgentType, ResponseStatus
from app.schemas.agent_request import AgentRequest
from app.schemas.agent_response import AgentResponse
from app.services.document.context_builder import (
    DocumentContextBuilder,
)
from app.services.document.document_keyword_search_service import (
    DocumentKeywordSearchService,
)
from app.services.document.document_hybrid_search_service import (
    DocumentHybridSearchService,
)
from app.services.document.document_rag_service import (
    DocumentRAGService,
)
from app.services.document.document_retriever_service import (
    DocumentRetriever,
)
from app.services.document.document_search_service import (
    DocumentSearchService,
)
from app.services.document.query_expansion_service import (
    QueryExpansionService,
)
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.storage.database.connection import get_connection
from app.api.dependencies.vectorstore import get_vector_provider


class RAGAgent(BaseAgent):
    """
    Agent responsible for answering document questions
    using retrieval-augmented generation.
    """

    def __init__(self) -> None:
        super().__init__()

        connection = get_connection()

        repository = DocumentChunkRepository(
            connection
        )

        keyword_service = DocumentKeywordSearchService(
            repository=repository,
        )

        semantic_service = DocumentSearchService(
            vector_provider=get_vector_provider(),
        )

        hybrid_service = DocumentHybridSearchService(
            semantic_search_service=semantic_service,
            keyword_search_service=keyword_service,
            query_expansion_service=QueryExpansionService(),
        )

        retriever = DocumentRetriever(
            search_service=hybrid_service,
        )

        self._rag_service = DocumentRAGService(
            retriever=retriever,
            context_builder=DocumentContextBuilder(),
        )

    def execute(
        self,
        request: AgentRequest,
    ) -> AgentResponse:

        self.logger.info(
            "Executing RAG Agent"
        )

        try:
            result = self._rag_service.answer(
                question=request.question,
                top_k=5,
                chat_history=request.chat_history,
            )

            request.context.selected_agent = AgentType.RAG

            self.logger.info(
                "RAG Agent execution completed"
            )

            citations = [
                source["source"]
                for source in result["sources"]
            ]

            return AgentResponse(
                answer=result["answer"],
                status=ResponseStatus.SUCCESS,
                message="RAG answer generated successfully.",
                data=result,
                citations=list(
                    dict.fromkeys(citations)
                ),
                metadata={
                    "agent": AgentType.RAG,
                    "source_count": len(
                        result["sources"]
                    ),
                },
            )

        except Exception as exc:
            self.logger.exception(
                "RAG Agent execution failed"
            )

            return AgentResponse(
                answer="",
                status=ResponseStatus.FAILED,
                message=str(exc),
                data=None,
                citations=[],
                metadata={
                    "agent": AgentType.RAG,
                },
            )

    def stream(
        self,
        request: AgentRequest,
    ) -> Iterator[str]:
        """
        Stream the RAG answer incrementally.
        """

        self.logger.info(
            "Starting RAG Agent streaming"
        )

        try:
            request.context.selected_agent = AgentType.RAG

            for chunk in self._rag_service.stream(
                question=request.question,
                top_k=5,
                chat_history=request.chat_history,
            ):
                yield chunk

            self.logger.info(
                "RAG Agent streaming completed"
            )

        except Exception:
            self.logger.exception(
                "RAG Agent streaming failed"
            )
            raise