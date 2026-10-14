
import time
from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.core.enums import AgentType, ResponseStatus
from app.schemas.agent_request import AgentRequest
from app.schemas.agent_response import AgentResponse
from app.services.document.context_builder import DocumentContextBuilder
from app.services.document.document_keyword_search_service import (
    DocumentKeywordSearchService,
)
from app.services.document.document_hybrid_search_service import (
    DocumentHybridSearchService,
)
from app.services.document.document_rag_service import DocumentRAGService
from app.services.document.document_retriever_service import DocumentRetriever
from app.services.document.document_search_service import DocumentSearchService
from app.services.document.query_expansion_service import QueryExpansionService
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.storage.database.connection import get_document_connection
from app.api.dependencies.vectorstore import get_vector_provider


class RAGAgent(BaseAgent):
    """Answer document questions using retrieval-augmented generation."""

    def __init__(self) -> None:
        super().__init__()

    def _build_rag_service(self, connection: Session) -> DocumentRAGService:
        """Build request-scoped services around the supplied DB session."""

        repository = DocumentChunkRepository(connection)

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

        retriever = DocumentRetriever(search_service=hybrid_service)

        return DocumentRAGService(
            retriever=retriever,
            context_builder=DocumentContextBuilder(),
        )

    def execute(self, request: AgentRequest) -> AgentResponse:
        start_time = time.perf_counter()
        source_count = 0

        self.logger.info("RAG Agent execution started")

        connection = get_document_connection()

        try:
            rag_service = self._build_rag_service(connection)

            result = rag_service.answer(
                question=request.question,
                chat_history=request.chat_history,
                document_id=request.attributes.get("document_id"),
                top_k=request.attributes.get("top_k", 5),
            )

            request.context.selected_agent = AgentType.RAG

            sources = result["sources"]
            source_count = len(sources)

            citations = list(
                dict.fromkeys(source["source"] for source in sources)
            )

            duration_ms = round(
                (time.perf_counter() - start_time) * 1000, 2
            )

            self.logger.info(
                "RAG Agent execution completed",
                extra={
                    "agent": str(AgentType.RAG),
                    "duration_ms": duration_ms,
                    "source_count": source_count,
                    "outcome": "success",
                },
            )

            return AgentResponse(
                answer=result["answer"],
                status=ResponseStatus.SUCCESS,
                message="RAG answer generated successfully.",
                data=result,
                citations=citations,
                metadata={
                    "agent": AgentType.RAG,
                    "source_count": source_count,
                },
            )

        except Exception:
            self.logger.exception(
                "RAG Agent execution failed",
                extra={
                    "agent": str(AgentType.RAG),
                    "duration_ms": round(
                        (time.perf_counter() - start_time) * 1000, 2
                    ),
                    "source_count": source_count,
                    "outcome": "failure",
                },
            )

            return AgentResponse(
                answer="",
                status=ResponseStatus.FAILED,
                message="Document question processing failed.",
                data=None,
                citations=[],
                metadata={"agent": AgentType.RAG},
            )

        finally:
            connection.close()

    def stream(self, request: AgentRequest) -> Iterator[str]:
        """Stream a RAG answer while keeping the session alive as needed."""

        start_time = time.perf_counter()
        outcome = "success"

        self.logger.info("RAG Agent streaming started")
        connection = get_document_connection()

        try:
            rag_service = self._build_rag_service(connection)
            request.context.selected_agent = AgentType.RAG

            yield from rag_service.stream(
                question=request.question,
                top_k=request.attributes.get("top_k", 5),
                document_id=request.attributes.get("document_id"),
                chat_history=request.chat_history,
            )

            self.logger.info("RAG Agent streaming completed")

        except Exception:
            outcome = "failure"
            self.logger.exception("RAG Agent streaming failed")
            raise

        finally:
            self.logger.info(
                "RAG Agent streaming finished",
                extra={
                    "agent": str(AgentType.RAG),
                    "duration_ms": round(
                        (time.perf_counter() - start_time) * 1000, 2
                    ),
                    "outcome": outcome,
                },
            )
            connection.close()
