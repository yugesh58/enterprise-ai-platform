from app.ai.llm import provider
from app.prompts.document_chat_prompt import (
    DOCUMENT_CHAT_PROMPT,
)
from app.schemas.chat import ChatResponse
from app.services.document.document_retriever_service import (
    DocumentRetriever,
)


class DocumentChatService:

    def __init__(
        self,
        retriever: DocumentRetriever,
    ) -> None:

        self._retriever = retriever

    def chat(
        self,
        question: str,
        top_k: int = 5,
        document_id: str | None = None,
    ) -> ChatResponse:

        context, sources = self._retriever.retrieve(
            query=question,
            top_k=top_k,
            document_id=document_id,
        )

        if not context:

            return ChatResponse(
                answer="I couldn't find any relevant information in the uploaded documents.",
                sources=[],
            )

        prompt = DOCUMENT_CHAT_PROMPT.format(
            context=context,
            question=question,
        )

        response = provider.invoke(prompt)

        return ChatResponse(
            answer=response.content,
            sources=sources,
        )