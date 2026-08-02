from app.ai.llm import provider
from app.schemas.chat import ChatResponse, SourceChunk
from app.services.document.document_search_service import (
    DocumentSearchService,
)
from app.prompts import document_chat_prompt


class DocumentChatService:

    def __init__(
        self,
        search_service: DocumentSearchService,
    ):
        self._search_service = search_service

    def chat(
        self,
        question: str,
        top_k: int = 5,
    ) -> ChatResponse:

        # -----------------------------------
        # Retrieve context
        # -----------------------------------

        chunks = self._search_service.search(
            query=question,
            top_k=top_k,
        )

        if not chunks:

            return ChatResponse(
                answer="I couldn't find any relevant information in the uploaded documents.",
                sources=[],
            )

        # -----------------------------------
        # Build Context
        # -----------------------------------

        context = "\n\n".join(
            chunk["payload"]["text"]
            for chunk in chunks
        )

        # -----------------------------------
        # Prompt
        # -----------------------------------

        prompt = document_chat_prompt

        # -----------------------------------
        # Call LLM
        # -----------------------------------

        response = provider.invoke(prompt)

        # -----------------------------------
        # Sources
        # -----------------------------------

        sources = [
            SourceChunk(
                source=chunk["payload"]["source"],
                page_number=chunk["payload"]["page_number"],
                score=chunk["score"],
                text=chunk["payload"]["text"],
            )
            for chunk in chunks
        ]

        return ChatResponse(
            answer=response.content,
            sources=sources,
        )