from app.services.document.document_hybrid_search_service import (
    DocumentHybridSearchService,
)
from app.services.document.retrieval_models import RetrievalResult


class DocumentRetriever:
    """
    Retrieves relevant document chunks for downstream RAG generation.

    Uses hybrid retrieval combining:
    - semantic vector search
    - PostgreSQL keyword search
    - query expansion
    - Reciprocal Rank Fusion
    """

    def __init__(
        self,
        search_service: DocumentHybridSearchService,
    ) -> None:
        self._search_service = search_service

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        document_id=None,
    ) -> list[RetrievalResult]:
        """
        Retrieve the most relevant document chunks.
        """

        return self._search_service.search(
            query=query,
            top_k=top_k,
            document_id=document_id,
        )