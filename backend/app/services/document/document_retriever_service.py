from uuid import UUID

from app.services.document.document_hybrid_search_service import (
    DocumentHybridSearchService,
)
from app.services.document.retrieval_models import RetrievalResult


class DocumentRetriever:
    """Retrieve relevant document chunks for downstream services."""

    def __init__(
        self,
        search_service: DocumentHybridSearchService,
    ) -> None:
        self._search_service = search_service

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        document_id: UUID | None = None,
    ) -> list[RetrievalResult]:
        """Return ranked retrieval results without formatting them."""

        return self._search_service.search(
            query=query,
            top_k=top_k,
            document_id=document_id,
        )
