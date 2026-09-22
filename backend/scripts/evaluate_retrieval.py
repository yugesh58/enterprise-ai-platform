from app.storage.database.connection import get_connection
from app.repositories.document_chunk_repository import DocumentChunkRepository

from app.services.document.document_keyword_search_service import (
    DocumentKeywordSearchService,
)
from app.services.document.document_search_service import (
    DocumentSearchService,
)
from app.services.document.document_hybrid_search_service import (
    DocumentHybridSearchService,
)
from app.services.document.query_expansion_service import (
    QueryExpansionService,
)

from app.api.dependencies.vectorstore import get_vector_provider


QUERIES = [
    "what skills does Yugesh possess?",
    "what AI technologies does Yugesh know?",
    "what experience does Yugesh have with Power Automate?",
    "what projects has Yugesh worked on?",
    "what databases does Yugesh use?",
]


def print_results(title, results):
    print(f"\n{title}")
    print("-" * 80)

    if not results:
        print("No results found.")
        return

    for rank, result in enumerate(results, start=1):
        if isinstance(result, dict):
            chunk_index = result["payload"].get("chunk_index")
            score = result["score"]
            text = result["payload"]["text"]

        else:
            chunk_index = result.chunk_index
            score = result.score
            text = result.text

        print(
            f"{rank}. chunk={chunk_index} "
            f"score={score:.4f}"
        )

        print(
            text[:180]
            .replace("\n", " ")
        )

        print()


def print_keyword_results(
    query: str,
    results: list[dict],
):
    print(f"\nQUERY: {query}")

    if not results:
        print("  No results found.")
        return

    for rank, result in enumerate(results, start=1):
        chunk_index = result["chunk_index"]
        score = result["keyword_score"]
        text = result["text"]

        print(
            f"  {rank}. "
            f"chunk={chunk_index} "
            f"score={score:.4f}"
        )

        print(
            f"     {text[:180].replace(chr(10), ' ')}"
        )


def main():
    connection = get_connection()

    try:
        # ---------------------------------------------------------
        # Repositories
        # ---------------------------------------------------------

        repository = DocumentChunkRepository(
            connection
        )

        # ---------------------------------------------------------
        # Services
        # ---------------------------------------------------------

        keyword_service = DocumentKeywordSearchService(
            repository=repository,
        )

        semantic_service = DocumentSearchService(
            vector_provider=get_vector_provider(),
        )

        query_expansion_service = QueryExpansionService()

        hybrid_service = DocumentHybridSearchService(
            semantic_search_service=semantic_service,
            keyword_search_service=keyword_service,
            query_expansion_service=query_expansion_service,
        )

        # ---------------------------------------------------------
        # Evaluate each query
        # ---------------------------------------------------------

        for query in QUERIES:

            print("\n")
            print("=" * 100)
            print(f"QUERY: {query}")
            print("=" * 100)

            # =====================================================
            # 1. Query expansion
            # =====================================================

            expanded_queries = query_expansion_service.expand(
                query
            )

            print("\nEXPANDED QUERIES")
            print("-" * 80)

            for expanded_query in expanded_queries:
                print(f"- {expanded_query}")

            # =====================================================
            # 2. Semantic retrieval
            # =====================================================

            semantic_results = semantic_service.search(
                query=query,
                top_k=5,
                apply_threshold=False,
            )

            print_results(
                "SEMANTIC",
                semantic_results,
            )

            # =====================================================
            # 3. Original keyword retrieval
            # =====================================================

            keyword_results = keyword_service.search(
                query=query,
                top_k=5,
            )

            print_results(
                "KEYWORD - ORIGINAL QUERY",
                keyword_results,
            )

            # =====================================================
            # 4. Expanded keyword retrieval
            # =====================================================

            print("\nEXPANDED KEYWORD SEARCH")
            print("-" * 80)

            all_expanded_keyword_results = []

            for expanded_query in expanded_queries:

                results = keyword_service.search(
                    query=expanded_query,
                    top_k=5,
                )

                print_keyword_results(
                    query=expanded_query,
                    results=results,
                )

                all_expanded_keyword_results.extend(
                    results
                )

            # =====================================================
            # 5. Hybrid retrieval
            # =====================================================

            hybrid_results = hybrid_service.search(
                query=query,
                top_k=5,
            )

            print_results(
                "HYBRID",
                hybrid_results,
            )

    finally:
        connection.close()


if __name__ == "__main__":
    main()