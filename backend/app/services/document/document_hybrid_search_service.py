
from uuid import UUID

from app.core.config import settings
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
    2. Original-query keyword search
    3. Query expansion and additional keyword search
    4. Result normalization
    5. Reciprocal Rank Fusion (RRF)
    6. Relevance filtering
    7. Return top-k results
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
        document_id: UUID | str | None = None,
    ) -> list[RetrievalResult]:
        """Perform hybrid document retrieval with relevance filtering."""

        if not query.strip() or top_k <= 0:
            return []

        if document_id is not None:
            try:
                document_id = UUID(str(document_id))
            except (ValueError, TypeError, AttributeError) as exc:
                raise ValueError(
                    "document_id must be a valid UUID"
                ) from exc

        candidate_k = max(top_k * 4, 20)
        document_id_filter = str(document_id) if document_id else None

        # 1. Semantic retrieval. Preserve raw similarity scores.
        semantic_results = self._semantic_search.search(
            query=query,
            top_k=candidate_k,
            document_id=document_id_filter,
            apply_threshold=False,
        )

        # 2. Search the original query to identify direct lexical evidence.
        original_keyword_results = self._keyword_search.search(
            query=query,
            top_k=candidate_k,
            document_id=document_id,
        )

        original_keyword_results = self._deduplicate_keyword_results(
            original_keyword_results
        )

        original_keyword_ids = {
            str(result["id"])
            for result in original_keyword_results
        }

        # 3. Preserve each expanded query as an independent ranking.
        expanded_queries = self._query_expansion.expand(query)
        keyword_rankings: list[tuple[list[RetrievalResult], float]] = []

        original_keyword_results = self._normalize_keyword_results(
            original_keyword_results
        )
        keyword_rankings.append((original_keyword_results, 2.0))

        seen_expansions = {query.strip().casefold()}

        for expanded_query in expanded_queries:
            normalized_query = expanded_query.strip().casefold()

            if not normalized_query or normalized_query in seen_expansions:
                continue

            seen_expansions.add(normalized_query)

            expanded_results = self._keyword_search.search(
                query=expanded_query,
                top_k=candidate_k,
                document_id=document_id,
            )

            expanded_results = self._deduplicate_keyword_results(
                expanded_results
            )

            normalized_results = self._normalize_keyword_results(
                expanded_results
            )

            if normalized_results:
                keyword_rankings.append((normalized_results, 0.5))

        # 4. Normalize semantic results.
        semantic = self._normalize_semantic_results(semantic_results)

        # 5. Fuse independent rankings and apply relevance filtering.
        return self._fuse_results(
            semantic_results=semantic,
            keyword_rankings=keyword_rankings,
            top_k=top_k,
            original_keyword_ids=original_keyword_ids,
        )

    def _normalize_semantic_results(
        self,
        results: list[dict],
    ) -> list[RetrievalResult]:
        """Normalize semantic results and retain the raw similarity score."""

        normalized: list[RetrievalResult] = []

        for result in results:
            payload = result["payload"]
            semantic_score = float(result["score"])

            normalized.append(
                RetrievalResult(
                    chunk_id=str(result["id"]),
                    document_id=str(payload["document_id"]),
                    text=payload["text"],
                    source=payload["source"],
                    page_number=payload["page_number"],
                    chunk_index=payload["chunk_index"],
                    score=semantic_score,
                    retrieval_type="semantic",
                    metadata={
                        **payload,
                        "semantic_score": semantic_score,
                    },
                )
            )

        return normalized

    def _normalize_keyword_results(
        self,
        results: list[dict],
    ) -> list[RetrievalResult]:
        """Normalize keyword results and retain their raw keyword scores."""

        normalized: list[RetrievalResult] = []

        for result in results:
            keyword_score = float(result["keyword_score"])

            normalized.append(
                RetrievalResult(
                    chunk_id=str(result["id"]),
                    document_id=str(result["document_id"]),
                    text=result["text"],
                    source=result["source"],
                    page_number=result["page_number"],
                    chunk_index=result["chunk_index"],
                    score=keyword_score,
                    retrieval_type="keyword",
                    metadata={
                        "keyword_score": keyword_score,
                    },
                )
            )

        return normalized

    def _deduplicate_keyword_results(
        self,
        results: list[dict],
    ) -> list[dict]:
        """
        Deduplicate keyword results.

        Keep the result with the highest keyword score for each chunk.
        """

        best_results: dict[str, dict] = {}

        for result in results:
            chunk_id = str(result["id"])
            existing = best_results.get(chunk_id)

            if (
                existing is None
                or float(result["keyword_score"])
                > float(existing["keyword_score"])
            ):
                best_results[chunk_id] = result

        return sorted(
            best_results.values(),
            key=lambda result: float(result["keyword_score"]),
            reverse=True,
        )

    def _fuse_results(
        self,
        semantic_results: list[RetrievalResult],
        keyword_rankings: list[tuple[list[RetrievalResult], float]],
        top_k: int,
        original_keyword_ids: set[str],
    ) -> list[RetrievalResult]:
        """
        Fuse independent rankings using weighted Reciprocal Rank Fusion.

        A result survives the relevance gate if:
        - its semantic score meets DOCUMENT_MIN_SCORE, or
        - the original user query produced a keyword match.

        Original-query keyword evidence receives greater weight than
        expanded-query evidence.
        """

        scores: dict[str, float] = {}
        results: dict[str, RetrievalResult] = {}

        rrf_k = 60

        # Semantic ranking: weight 1.0.
        for rank, result in enumerate(semantic_results, start=1):
            chunk_id = result.chunk_id
            scores[chunk_id] = scores.get(chunk_id, 0.0) + (
                1.0 / (rrf_k + rank)
            )
            results[chunk_id] = result

        # Each keyword query contributes its own independent ranking.
        for keyword_results, weight in keyword_rankings:
            for rank, result in enumerate(keyword_results, start=1):
                chunk_id = result.chunk_id
                scores[chunk_id] = scores.get(chunk_id, 0.0) + (
                    weight / (rrf_k + rank)
                )

                if chunk_id not in results:
                    result.metadata = dict(result.metadata or {})
                    results[chunk_id] = result

                existing = results[chunk_id]
                if existing.metadata is None:
                    existing.metadata = {}

                previous_score = existing.metadata.get("keyword_score", 0.0)
                existing.metadata["keyword_score"] = max(
                    float(previous_score),
                    float(result.score),
                )
                existing.metadata["original_keyword_match"] = (
                    chunk_id in original_keyword_ids
                )

        ranked = sorted(
            results.values(),
            key=lambda result: scores[result.chunk_id],
            reverse=True,
        )

        # Preserve the original relevance gate.
        ranked = [
            result
            for result in ranked
            if (
                (
                    result.metadata is not None
                    and result.metadata.get("semantic_score", 0.0)
                    >= settings.DOCUMENT_MIN_SCORE
                )
                or result.chunk_id in original_keyword_ids
            )
        ]

        final_results = []

        for result in ranked[:top_k]:
            result.score = scores[result.chunk_id]
            result.retrieval_type = "hybrid"
            final_results.append(result)

        return final_results
