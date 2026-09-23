from app.services.document.context_builder import (
    DocumentContextBuilder,
)
from app.services.document.retrieval_models import RetrievalResult


def main():
    results = [
        RetrievalResult(
            chunk_id="chunk-1",
            document_id="document-1",
            text=(
                "Yugesh has experience with Generative AI, "
                "Machine Learning, LangChain, and Power Platform."
            ),
            source="Yugesh_Bhadwal_Resume.pdf",
            page_number=1,
            chunk_index=6,
            score=0.0320,
            retrieval_type="hybrid",
        ),
        RetrievalResult(
            chunk_id="chunk-2",
            document_id="document-1",
            text=(
                "He has worked with Power Automate, "
                "Copilot Studio, and Azure OpenAI."
            ),
            source="Yugesh_Bhadwal_Resume.pdf",
            page_number=1,
            chunk_index=7,
            score=0.0315,
            retrieval_type="hybrid",
        ),
    ]

    builder = DocumentContextBuilder()

    context = builder.build(results)

    print("=" * 80)
    print("GENERATED CONTEXT")
    print("=" * 80)
    print(context)


if __name__ == "__main__":
    main()