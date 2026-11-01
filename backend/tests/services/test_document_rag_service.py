from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.services.document.document_rag_service import DocumentRAGService
from app.services.document.retrieval_models import RetrievalResult


@pytest.fixture
def dependencies():
    retriever = Mock()
    context_builder = Mock()
    context_builder.build.return_value = "Document context"

    llm_provider = Mock()
    llm_provider.invoke.return_value = SimpleNamespace(
        content="Grounded answer"
    )

    return retriever, context_builder, llm_provider


@pytest.fixture
def rag_service(dependencies):
    retriever, context_builder, llm_provider = dependencies

    return DocumentRAGService(
        retriever=retriever,
        context_builder=context_builder,
        llm_provider=llm_provider,
    )


@pytest.mark.parametrize("retrieval_type", ["semantic", "keyword"])
def test_answer_preserves_source_attribution(
    rag_service,
    dependencies,
    retrieval_type,
):
    retriever, _, _ = dependencies

    document = RetrievalResult(
        chunk_id="chunk-1",
        document_id=str(uuid4()),
        text="Employee leave policy content",
        source="employee_policy.pdf",
        page_number=4,
        chunk_index=12,
        score=0.8,
        retrieval_type=retrieval_type,
        metadata={},
    )
    retriever.retrieve.return_value = [document]

    result = rag_service.answer(
        question="How do employees request leave?"
    )

    assert result["sources"] == [
        {
            "source": "employee_policy.pdf",
            "page_number": 4,
            "chunk_index": 12,
        }
    ]


def test_answer_uses_metadata_source_fallback(
    rag_service,
    dependencies,
):
    retriever, _, _ = dependencies
    retriever.retrieve.return_value = [
        SimpleNamespace(
            metadata={"source": "fallback.pdf"},
            page_number=2,
            chunk_index=5,
        )
    ]

    result = rag_service.answer(question="What is in the document?")

    assert result["sources"] == [
        {
            "source": "fallback.pdf",
            "page_number": 2,
            "chunk_index": 5,
        }
    ]


def test_answer_uses_unknown_when_source_is_unavailable(
    rag_service,
    dependencies,
):
    retriever, _, _ = dependencies
    retriever.retrieve.return_value = [
        SimpleNamespace(metadata={})
    ]

    result = rag_service.answer(question="What is in the document?")

    assert result["sources"] == [
        {
            "source": "Unknown",
            "page_number": None,
            "chunk_index": None,
        }
    ]
