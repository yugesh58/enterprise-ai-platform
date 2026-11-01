
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.core.config import settings
from app.services.document.document_hybrid_search_service import (
    DocumentHybridSearchService,
)
from app.services.document.retrieval_models import RetrievalResult


@pytest.fixture
def service():
    return DocumentHybridSearchService(
        semantic_search_service=MagicMock(),
        keyword_search_service=MagicMock(),
        query_expansion_service=MagicMock(),
    )


def make_result(
    chunk_id: str,
    score: float,
    retrieval_type: str,
    *,
    semantic_score: float | None = None,
) -> RetrievalResult:
    metadata = {}

    if semantic_score is not None:
        metadata["semantic_score"] = semantic_score

    return RetrievalResult(
        chunk_id=chunk_id,
        document_id=str(uuid4()),
        text=f"Text for {chunk_id}",
        source="test.txt",
        page_number=1,
        chunk_index=0,
        score=score,
        retrieval_type=retrieval_type,
        metadata=metadata,
    )


def test_relevant_semantic_result_survives(service):
    result = make_result(
        "relevant",
        0.8,
        "semantic",
        semantic_score=settings.DOCUMENT_MIN_SCORE + 0.1,
    )

    results = service._fuse_results(
        semantic_results=[result],
        keyword_rankings=[],
        top_k=5,
        original_keyword_ids=set(),
    )

    assert len(results) == 1
    assert results[0].chunk_id == "relevant"
    assert results[0].retrieval_type == "hybrid"


def test_weak_semantic_result_without_keyword_match_is_filtered(service):
    result = make_result(
        "irrelevant",
        0.2,
        "semantic",
        semantic_score=settings.DOCUMENT_MIN_SCORE - 0.1,
    )

    results = service._fuse_results(
        semantic_results=[result],
        keyword_rankings=[],
        top_k=5,
        original_keyword_ids=set(),
    )

    assert results == []


def test_original_keyword_match_survives_low_semantic_score(service):
    result = make_result(
        "exact-match",
        0.2,
        "semantic",
        semantic_score=settings.DOCUMENT_MIN_SCORE - 0.1,
    )

    results = service._fuse_results(
        semantic_results=[result],
        keyword_rankings=[],
        top_k=5,
        original_keyword_ids={"exact-match"},
    )

    assert len(results) == 1
    assert results[0].chunk_id == "exact-match"


def test_no_candidates_returns_empty_list(service):
    results = service._fuse_results(
        semantic_results=[],
        keyword_rankings=[],
        top_k=5,
        original_keyword_ids=set(),
    )

    assert results == []


def test_rrf_order_is_preserved_after_filtering(service):
    relevant_first = make_result(
        "first",
        0.9,
        "semantic",
        semantic_score=settings.DOCUMENT_MIN_SCORE + 0.2,
    )
    irrelevant = make_result(
        "irrelevant",
        0.1,
        "semantic",
        semantic_score=settings.DOCUMENT_MIN_SCORE - 0.2,
    )
    relevant_second = make_result(
        "second",
        0.8,
        "semantic",
        semantic_score=settings.DOCUMENT_MIN_SCORE + 0.1,
    )

    results = service._fuse_results(
        semantic_results=[
            relevant_first,
            irrelevant,
            relevant_second,
        ],
        keyword_rankings=[],
        top_k=5,
        original_keyword_ids=set(),
    )

    assert [result.chunk_id for result in results] == [
        "first",
        "second",
    ]
    assert results[0].score > results[1].score



def test_semantic_search_receives_requested_candidate_limit():
    from unittest.mock import patch

    from app.services.document.document_search_service import (
        DocumentSearchService,
    )

    provider = MagicMock()
    embeddings = MagicMock()
    embeddings.embed_query.return_value = [0.1, 0.2]
    provider.search.return_value = []

    with patch(
        "app.services.document.document_search_service.get_embeddings",
        return_value=embeddings,
    ):
        search_service = DocumentSearchService(provider)

    search_service.search(
        query="employee leave policy",
        top_k=28,
        apply_threshold=False,
    )

    assert provider.search.call_args.kwargs["limit"] == 28


def test_hybrid_search_requests_candidate_k_from_semantic_service(service):
    service._semantic_search.search.return_value = []
    service._keyword_search.search.return_value = []
    service._query_expansion.expand.return_value = []

    service.search(query="employee leave policy", top_k=7)

    assert service._semantic_search.search.call_args.kwargs["top_k"] == 28


def test_weighted_rrf_prioritizes_original_keyword_ranking(service):
    original_result = make_result("original", 0.4, "keyword")
    expanded_result = make_result(
        "expanded",
        0.5,
        "semantic",
        semantic_score=settings.DOCUMENT_MIN_SCORE + 0.1,
    )

    results = service._fuse_results(
        semantic_results=[expanded_result],
        keyword_rankings=[
            ([original_result], 2.0),
            ([make_result("expanded", 0.5, "keyword")], 0.5),
        ],
        top_k=5,
        original_keyword_ids={"original"},
    )

    scores = {result.chunk_id: result.score for result in results}

    assert "original" in scores
    assert "expanded" in scores
    assert scores["original"] > scores["expanded"]



def test_hybrid_search_normalizes_string_document_id(service):
    document_id = uuid4()

    service._semantic_search.search.return_value = []
    service._keyword_search.search.return_value = []
    service._query_expansion.expand.return_value = []

    service.search(
        query="employee leave policy",
        document_id=str(document_id),
    )

    assert (
        service._keyword_search.search.call_args.kwargs["document_id"]
        == document_id
    )
    assert (
        service._semantic_search.search.call_args.kwargs["document_id"]
        == str(document_id)
    )


def test_hybrid_search_rejects_invalid_document_id(service):
    with pytest.raises(ValueError, match="valid UUID"):
        service.search(
            query="employee leave policy",
            document_id="not-a-valid-uuid",
        )
