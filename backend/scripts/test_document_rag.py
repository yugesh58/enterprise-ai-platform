from app.services.document.context_builder import (
    DocumentContextBuilder,
)
from app.services.document.document_keyword_search_service import (
    DocumentKeywordSearchService,
)
from app.services.document.document_hybrid_search_service import (
    DocumentHybridSearchService,
)
from app.services.document.document_rag_service import (
    DocumentRAGService,
)
from app.services.document.document_retriever_service import (
    DocumentRetriever,
)
from app.services.document.document_search_service import (
    DocumentSearchService,
)
from app.services.document.query_expansion_service import (
    QueryExpansionService,
)
from app.storage.database.connection import get_connection
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.api.dependencies.vectorstore import get_vector_provider


QUESTION = "What AI technologies does Yugesh know?"


def build_rag_service() -> DocumentRAGService:
    connection = get_connection()

    repository = DocumentChunkRepository(
        connection
    )

    keyword_service = DocumentKeywordSearchService(
        repository=repository,
    )

    semantic_service = DocumentSearchService(
        vector_provider=get_vector_provider(),
    )

    hybrid_service = DocumentHybridSearchService(
        semantic_search_service=semantic_service,
        keyword_search_service=keyword_service,
        query_expansion_service=QueryExpansionService(),
    )

    retriever = DocumentRetriever(
        search_service=hybrid_service,
    )

    return DocumentRAGService(
        retriever=retriever,
        context_builder=DocumentContextBuilder(),
    )


def main():
    rag_service = build_rag_service()

    result = rag_service.answer(
        question=QUESTION,
        top_k=5,
    )

    print("=" * 100)
    print("QUESTION")
    print("=" * 100)
    print(QUESTION)

    print("\n")
    print("=" * 100)
    print("ANSWER")
    print("=" * 100)
    print(result["answer"])

    print("\n")
    print("=" * 100)
    print("SOURCES")
    print("=" * 100)

    for index, source in enumerate(
        result["sources"],
        start=1,
    ):
        print(
            f"{index}. "
            f"source={source['source']} | "
            f"page={source['page_number']} | "
            f"chunk={source['chunk_index']} | "
            f"score={source['score']:.4f}"
        )


if __name__ == "__main__":
    main()