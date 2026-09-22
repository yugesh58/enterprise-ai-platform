from typing import Optional

from app.ai.embeddings import get_embeddings
from app.core.config import settings
from app.storage.vectorstore.base import VectorProvider


class DocumentSearchService:
    """
    Service responsible for semantic document retrieval.
    """

    def __init__(
        self,
        vector_provider: VectorProvider,
    ) -> None:
        self._vector_provider = vector_provider
        self._embeddings = get_embeddings()

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
        apply_threshold: bool = True,
    ) -> list[dict]:
        """
        Perform semantic search against the vector store.

        Args:
            query: User search query.
            top_k: Number of results to return.
            document_id: Optional document filter.
            apply_threshold: Whether to apply the configured minimum
                similarity score.

        The hybrid retrieval layer can disable the threshold so that
        low-scoring but potentially useful candidates are available
        during fusion.
        """

        query_embedding = self._embeddings.embed_query(query)

        filters = (
            {"document_id": document_id}
            if document_id
            else None
        )

        results = self._vector_provider.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=query_embedding,
            limit=settings.DOCUMENT_SEARCH_LIMIT,
            filters=filters,
        )

        if apply_threshold:
            results = [
                result
                for result in results
                if result["score"] >= settings.DOCUMENT_MIN_SCORE
            ]

        seen = set()
        unique_results = []

        for result in results:
            payload = result["payload"]

            key = (
                payload.get("document_id"),
                payload.get("page_number"),
                payload.get("text"),
            )

            if key in seen:
                continue

            seen.add(key)
            unique_results.append(result)

        return unique_results[:top_k]