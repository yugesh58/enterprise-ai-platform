from app.ai.llm import provider
from app.prompts.document_chat_prompt import DOCUMENT_CHAT_PROMPT
from app.schemas.chat import ChatResponse
from app.services.document.document_retriever_service import (
    DocumentRetriever,
)


class DocumentChatService:
    """Generate answers grounded in retrieved document chunks."""

    def __init__(self, retriever: DocumentRetriever) -> None:
        self._retriever = retriever

    def chat(
        self,
        question: str,
        top_k: int = 5,
        document_id: str | None = None,
    ) -> ChatResponse:
        results = self._retriever.retrieve(
            query=question,
            top_k=top_k,
            document_id=document_id,
        )

        if not results:
            return ChatResponse(
                answer=(
                    "I couldn't find any relevant information "
                    "in the uploaded documents."
                ),
                sources=[],
            )

        context_parts = []
        sources = []

        for result in results:
            context_parts.append(
                f"Source: {result.source}\n"
                f"Page: {result.page_number}\n"
                f"Content:\n{result.text}"
            )

            sources.append(
                {
                    "source": result.source,
                    "page_number": result.page_number,
                    "score": result.score,
                    "text": result.text,
                }
            )

        prompt = DOCUMENT_CHAT_PROMPT.format(
            context="\n\n---\n\n".join(context_parts),
            question=question,
        )

        response = provider.invoke(prompt)

        return ChatResponse(
            answer=response.content,
            sources=sources,
        )
