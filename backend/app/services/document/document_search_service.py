from typing import Optional

from app.ai.embeddings import get_embeddings
from app.core.config import settings
from app.storage.vectorstore.base import VectorProvider


class DocumentSearchService:
    """
    Performs semantic search over indexed documents.
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
    ) -> list[dict]:

        query_embedding = self._embeddings.embed_query(query)

        filters = None

        if document_id:
            filters = {
                "document_id": document_id
            }

        # Retrieve more candidates than required
        results = self._vector_provider.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=query_embedding,
            limit=settings.DOCUMENT_SEARCH_LIMIT,
            filters=filters,
        )

        # Filter low-confidence results
        results = [
            result
            for result in results
            if result["score"] >= settings.DOCUMENT_MIN_SCORE
        ]

        # Remove duplicate chunks
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