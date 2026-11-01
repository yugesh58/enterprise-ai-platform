import pytest

from app.services.document.query_expansion_service import QueryExpansionService


def test_original_query_is_preserved():
    service = QueryExpansionService()
    query = "What projects have you built using Power Automate?"

    assert service.expand(query)[-1] == query


def test_expansion_is_bounded():
    service = QueryExpansionService(max_expansions=3)
    query = "What projects have you built using Power Automate and Azure OpenAI?"

    results = service.expand(query)

    assert len(results) <= 4
    assert results[-1] == query


def test_expansion_removes_duplicates():
    results = QueryExpansionService().expand(
        "Power Automate Power Automate"
    )

    normalized = [item.casefold() for item in results]
    assert len(normalized) == len(set(normalized))


def test_empty_query_returns_empty_list():
    assert QueryExpansionService().expand("   ") == []


def test_zero_expansions_preserves_original():
    assert QueryExpansionService(max_expansions=0).expand(
        "Power Automate"
    ) == ["Power Automate"]


def test_negative_expansion_limit_is_rejected():
    with pytest.raises(ValueError):
        QueryExpansionService(max_expansions=-1)
