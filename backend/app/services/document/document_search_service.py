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

        print("\n" + "=" * 80)
        print("DOCUMENT SEARCH")
        print("=" * 80)
        print(f"Query: {query}")

        query_embedding = self._embeddings.embed_query(query)
        print("Query embedding dimension:", len(query_embedding))

        filters = None

        if document_id:
            filters = {
                "document_id": document_id
            }

        results = self._vector_provider.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=query_embedding,
            limit=top_k,
            filters=filters,
        )

        print(f"Retrieved {len(results)} chunks")
        for i, r in enumerate(results):
            print(f"\nResult {i + 1}")
            print(r)
        return results