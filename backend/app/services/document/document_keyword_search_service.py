from app.repositories.document_chunk_repository import DocumentChunkRepository


class DocumentKeywordSearchService:

    def __init__(self, repository: DocumentChunkRepository):
        self._repository = repository

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: str | None = None,
    ):
        """
        Returns chunks containing query terms.

        This is intentionally simple.
        Later this can be replaced with BM25.
        """
        return self._repository.keyword_search(
            query=query,
            top_k=top_k,
            document_id=document_id,
        )