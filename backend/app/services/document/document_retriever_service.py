from app.schemas.chat import SourceChunk
from app.services.document.document_search_service import (
    DocumentSearchService,
)


class DocumentRetriever:
    """
    Responsible for retrieving, deduplicating and formatting
    document context for the LLM.
    """

    def __init__(
        self,
        search_service: DocumentSearchService,
    ) -> None:

        self._search_service = search_service

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        document_id: str | None = None,
    ) -> tuple[str, list[SourceChunk]]:

        chunks = self._search_service.search(
            query=query,
            top_k=top_k,
            document_id=document_id,
        )

        chunks = self._deduplicate(chunks)

        if not chunks:
            return "", []

        context = self._build_context(chunks)

        sources = [
            SourceChunk(
                source=chunk["payload"]["source"],
                page_number=chunk["payload"]["page_number"],
                score=chunk["score"],
                text=chunk["payload"]["text"],
            )
            for chunk in chunks
        ]

        return context, sources

    def _deduplicate(
        self,
        chunks: list[dict],
    ) -> list[dict]:

        seen = set()
        unique = []

        for chunk in chunks:

            payload = chunk["payload"]

            key = (
                payload["source"],
                payload["page_number"],
                payload["text"],
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(chunk)

        return unique

    def _build_context(
        self,
        chunks: list[dict],
    ) -> str:

        sections = []

        for chunk in chunks:

            payload = chunk["payload"]

            sections.append(
                f"""
==================================================
Document : {payload["source"]}
Page     : {payload["page_number"]}
Similarity: {chunk["score"]:.3f}

Content:
{payload["text"]}
""".strip()
            )

        return "\n\n".join(sections)