from app.services.document.retrieval_models import RetrievalResult


class DocumentContextBuilder:
    """
    Builds structured context from retrieved document chunks.

    The context produced here is passed to the LLM as the
    only source of factual information for RAG generation.
    """

    def build(
        self,
        results: list[RetrievalResult],
    ) -> str:
        """
        Convert retrieved chunks into a structured context string.
        """

        if not results:
            return "No relevant document context was found."

        context_parts: list[str] = []

        for index, result in enumerate(
            results,
            start=1,
        ):
            context_parts.append(
                self._format_result(
                    index=index,
                    result=result,
                )
            )

        return "\n\n".join(context_parts)

    def _format_result(
        self,
        index: int,
        result: RetrievalResult,
    ) -> str:
        """
        Format a single retrieval result.
        """

        return (
            f"[Context {index}]\n"
            f"Source: {result.source}\n"
            f"Page: {result.page_number}\n"
            f"Chunk: {result.chunk_index}\n"
            f"Content:\n"
            f"{result.text}"
        )