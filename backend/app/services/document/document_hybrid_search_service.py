from uuid import UUID

from app.services.document.document_keyword_search_service import (
    DocumentKeywordSearchService,
)
from app.services.document.document_search_service import DocumentSearchService
from app.services.document.retrieval_models import RetrievalResult
from app.services.document.query_expansion_service import (
    QueryExpansionService,
)


class DocumentHybridSearchService:
    """
    Combines semantic and keyword retrieval into a single ranked result set.

    Retrieval pipeline:
    1. Semantic vector search
    2. Query expansion
    3. PostgreSQL keyword search
    4. Result normalization
    5. Reciprocal Rank Fusion (RRF)
    6. Deduplication
    """

    def __init__(
        self,
        semantic_search_service: DocumentSearchService,
        keyword_search_service: DocumentKeywordSearchService,
        query_expansion_service: QueryExpansionService,
    ) -> None:
        self._semantic_search = semantic_search_service
        self._keyword_search = keyword_search_service
        self._query_expansion = query_expansion_service

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: UUID | None = None,
    ) -> list[RetrievalResult]:
        """
        Perform hybrid document retrieval.

        Combines:
        - semantic retrieval from the vector database
        - keyword retrieval from PostgreSQL
        - query expansion
        - Reciprocal Rank Fusion
        """

        candidate_k = max(top_k * 4, 20)

        # ---------------------------------------------------------
        # 1. Semantic retrieval
        # ---------------------------------------------------------

        semantic_results = self._semantic_search.search(
            query=query,
            top_k=candidate_k,
            document_id=str(document_id) if document_id else None,
            apply_threshold=False,
        )

        # ---------------------------------------------------------
        # 2. Query expansion
        # ---------------------------------------------------------

        expanded_queries = self._query_expansion.expand(query)

        # ---------------------------------------------------------
        # 3. Keyword retrieval
        # ---------------------------------------------------------

        keyword_results: list[dict] = []

        for expanded_query in expanded_queries:
            keyword_results.extend(
                self._keyword_search.search(
                    query=expanded_query,
                    top_k=candidate_k,
                    document_id=document_id,
                )
            )

        # Remove duplicate keyword results while keeping
        # the strongest keyword score for each chunk.
        keyword_results = self._deduplicate_keyword_results(
            keyword_results
        )

        # ---------------------------------------------------------
        # 4. Normalize results
        # ---------------------------------------------------------

        semantic = self._normalize_semantic_results(
            semantic_results
        )

        keyword = self._normalize_keyword_results(
            keyword_results
        )

        # ---------------------------------------------------------
        # 5. Fuse results using Reciprocal Rank Fusion
        # ---------------------------------------------------------

        return self._fuse_results(
            semantic_results=semantic,
            keyword_results=keyword,
            top_k=top_k,
        )

    def _normalize_semantic_results(
        self,
        results: list[dict],
    ) -> list[RetrievalResult]:
        """
        Convert semantic search results into RetrievalResult objects.
        """

        normalized: list[RetrievalResult] = []

        for result in results:
            payload = result["payload"]

            normalized.append(
                RetrievalResult(
                    chunk_id=str(result["id"]),
                    document_id=str(payload["document_id"]),
                    text=payload["text"],
                    source=payload["source"],
                    page_number=payload["page_number"],
                    chunk_index=payload["chunk_index"],
                    score=float(result["score"]),
                    retrieval_type="semantic",
                    metadata=payload,
                )
            )

        return normalized

    def _normalize_keyword_results(
        self,
        results: list[dict],
    ) -> list[RetrievalResult]:
        """
        Convert PostgreSQL keyword search results into
        RetrievalResult objects.
        """

        normalized: list[RetrievalResult] = []

        for result in results:
            normalized.append(
                RetrievalResult(
                    chunk_id=str(result["id"]),
                    document_id=str(result["document_id"]),
                    text=result["text"],
                    source=result["source"],
                    page_number=result["page_number"],
                    chunk_index=result["chunk_index"],
                    score=float(result["keyword_score"]),
                    retrieval_type="keyword",
                )
            )

        return normalized

    def _deduplicate_keyword_results(
        self,
        results: list[dict],
    ) -> list[dict]:
        """
        Deduplicate keyword search results.

        The same chunk can appear multiple times because
        query expansion performs multiple keyword searches.

        For duplicate chunks, keep the result with the
        highest keyword score.
        """

        best_results: dict[str, dict] = {}

        for result in results:
            chunk_id = str(result["id"])

            existing = best_results.get(chunk_id)

            if (
                existing is None
                or result["keyword_score"]
                > existing["keyword_score"]
            ):
                best_results[chunk_id] = result

        return list(best_results.values())

    def _fuse_results(
        self,
        semantic_results: list[RetrievalResult],
        keyword_results: list[RetrievalResult],
        top_k: int,
    ) -> list[RetrievalResult]:
        """
        Combine semantic and keyword rankings using
        Reciprocal Rank Fusion (RRF).

        RRF score:

            1 / (k + rank)

        where k is a constant used to reduce the impact
        of very high rankings.

        A chunk appearing in both retrieval systems receives
        contributions from both rankings.
        """

        scores: dict[str, float] = {}
        results: dict[str, RetrievalResult] = {}

        rrf_k = 60

        # ---------------------------------------------------------
        # Semantic results
        # ---------------------------------------------------------

        for rank, result in enumerate(
            semantic_results,
            start=1,
        ):
            chunk_id = result.chunk_id

            scores[chunk_id] = scores.get(
                chunk_id,
                0.0,
            )

            scores[chunk_id] += 1.0 / (
                rrf_k + rank
            )

            results[chunk_id] = result

        # ---------------------------------------------------------
        # Keyword results
        # ---------------------------------------------------------

        for rank, result in enumerate(
            keyword_results,
            start=1,
        ):
            chunk_id = result.chunk_id

            scores[chunk_id] = scores.get(
                chunk_id,
                0.0,
            )

            scores[chunk_id] += 1.0 / (
                rrf_k + rank
            )

            # Keep the existing semantic result if the chunk
            # already exists in the combined result set.
            if chunk_id not in results:
                results[chunk_id] = result

        # ---------------------------------------------------------
        # Sort using the actual RRF score
        # ---------------------------------------------------------

        ranked = sorted(
            results.values(),
            key=lambda result: scores[result.chunk_id],
            reverse=True,
        )

        # ---------------------------------------------------------
        # Return results with the actual hybrid score
        # ---------------------------------------------------------

        final_results: list[RetrievalResult] = []

        for result in ranked[:top_k]:
            result.score = scores[result.chunk_id]
            result.retrieval_type = "hybrid"

            final_results.append(result)

        return final_results