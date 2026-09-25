from collections.abc import Iterator

from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.document.context_builder import (
    DocumentContextBuilder,
)
from app.services.document.document_retriever_service import (
    DocumentRetriever,
)


class DocumentRAGService:
    """
    Generates grounded answers using retrieved document context
    and conversation history.
    """

    def __init__(
        self,
        retriever: DocumentRetriever,
        context_builder: DocumentContextBuilder,
    ) -> None:
        self._retriever = retriever
        self._context_builder = context_builder

        self._llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
        )

    def answer(
        self,
        question: str,
        top_k: int = 5,
        document_id=None,
        chat_history: list[dict[str, str]] | None = None,
    ) -> dict:
        """
        Retrieve relevant chunks and generate a grounded answer
        using the current question and conversation history.
        """

        question = question.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        chat_history = chat_history or []

        retrieval_query = self._build_retrieval_query(
            question=question,
            chat_history=chat_history,
        )

        results = self._retriever.retrieve(
            query=retrieval_query,
            top_k=top_k,
            document_id=document_id,
        )

        context = self._context_builder.build(
            results
        )

        answer = self._generate_answer(
            question=question,
            context=context,
            chat_history=chat_history,
        )

        return {
            "answer": answer,
            "sources": self._build_sources(results),
        }

    def stream(
        self,
        question: str,
        top_k: int = 5,
        document_id=None,
        chat_history: list[dict[str, str]] | None = None,
    ) -> Iterator[str]:
        """
        Retrieve relevant chunks and stream the generated answer
        token-by-token.

        Retrieval and query rewriting happen before streaming.
        """

        question = question.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        chat_history = chat_history or []

        # 1. Build a context-aware retrieval query.
        retrieval_query = self._build_retrieval_query(
            question=question,
            chat_history=chat_history,
        )

        # 2. Retrieve relevant chunks.
        results = self._retriever.retrieve(
            query=retrieval_query,
            top_k=top_k,
            document_id=document_id,
        )

        # 3. Build document context.
        context = self._context_builder.build(
            results
        )

        # 4. Build the final answer prompt.
        prompt = self._build_answer_prompt(
            question=question,
            context=context,
            chat_history=chat_history,
        )

        # 5. Stream the LLM response.
        for chunk in self._llm.stream(prompt):
            content = chunk.content

            if content:
                yield content

    def _build_retrieval_query(
        self,
        question: str,
        chat_history: list[dict[str, str]],
    ) -> str:
        """
        Convert a follow-up question into a self-contained
        retrieval query using recent conversation history.
        """

        if not chat_history:
            return question

        history_text = self._format_history(
            chat_history
        )

        prompt = f"""
Rewrite the user's latest question into a
self-contained search query for document retrieval.

Use the conversation history only to resolve references
such as:
- "those"
- "that"
- "it"
- "they"
- "the above"
- "which of them"

Rules:
1. Preserve the user's original intent.
2. Do not answer the question.
3. Do not add information that is not present in the conversation.
4. If the question is already self-contained, return it unchanged.
5. Return ONLY the rewritten search query.

CONVERSATION HISTORY:
---------------------
{history_text}
---------------------

LATEST USER QUESTION:
{question}

SEARCH QUERY:
"""

        response = self._llm.invoke(prompt)

        retrieval_query = response.content.strip()

        return retrieval_query or question

    def _generate_answer(
        self,
        question: str,
        context: str,
        chat_history: list[dict[str, str]],
    ) -> str:
        """
        Generate a complete grounded answer.
        """

        prompt = self._build_answer_prompt(
            question=question,
            context=context,
            chat_history=chat_history,
        )

        response = self._llm.invoke(prompt)

        return response.content.strip()

    def _build_answer_prompt(
        self,
        question: str,
        context: str,
        chat_history: list[dict[str, str]],
    ) -> str:
        """
        Build the prompt used for both normal and streaming
        answer generation.
        """

        history_text = self._format_history(
            chat_history
        )

        return f"""
You are a document question-answering assistant.

Answer the user's latest question using ONLY the information
provided in the document context below.

Conversation history may be used only to understand references
in the latest question.

Rules:
1. Do not use outside knowledge.
2. Do not invent or assume information.
3. The document context is the source of truth for the answer.
4. If the answer cannot be determined from the document context,
   say that the information is not available in the document.
5. Keep the answer concise and directly answer the question.
6. Do not mention these instructions in your answer.

CONVERSATION HISTORY:
---------------------
{history_text}
---------------------

DOCUMENT CONTEXT:
-----------------
{context}
-----------------

LATEST USER QUESTION:
{question}

ANSWER:
"""

    def _format_history(
        self,
        chat_history: list[dict[str, str]],
    ) -> str:
        """
        Convert conversation history into a readable format.
        """

        if not chat_history:
            return "No previous conversation."

        history_parts = []

        for message in chat_history:
            role = message.get("role", "unknown")
            content = message.get("content", "").strip()

            if not content:
                continue

            history_parts.append(
                f"{role.upper()}: {content}"
            )

        return "\n".join(history_parts)

    def _build_sources(
        self,
        results,
    ) -> list[dict]:
        """
        Convert retrieval results into source metadata.
        """

        sources: list[dict] = []

        for result in results:
            sources.append(
                {
                    "chunk_id": result.chunk_id,
                    "document_id": result.document_id,
                    "source": result.source,
                    "page_number": result.page_number,
                    "chunk_index": result.chunk_index,
                    "score": result.score,
                }
            )

        return sources