
from collections.abc import Iterator

from app.ai.providers.base_provider import BaseLLMProvider
from app.services.document.context_builder import DocumentContextBuilder
from app.services.document.document_retriever_service import DocumentRetriever


class DocumentRAGService:
    def __init__(
        self,
        retriever: DocumentRetriever,
        context_builder: DocumentContextBuilder,
        llm_provider: BaseLLMProvider,
    ) -> None:
        self._retriever = retriever
        self._context_builder = context_builder
        self._llm_provider = llm_provider

    def answer(
        self,
        question: str,
        top_k: int = 5,
        document_id: str | None = None,
        conversation_id: str | None = None,
        chat_history: list[dict[str, str]] | None = None,
    ) -> str:
        retrieval_query = self._build_retrieval_query(
            question=question,
            history=history,
        )

        documents = self._retriever.retrieve(
            query=retrieval_query,
            top_k=top_k,
            document_id=document_id,
        )

        context = self._context_builder.build(documents)

        return self._generate_answer(
            question=question,
            context=context,
            history=history,
        )

    def stream(
        self,
        question: str,
        top_k: int = 5,
        document_id: str | None = None,
        conversation_id: str | None = None,
        chat_history: list[dict[str, str]] | None = None,
    ) -> Iterator[str]:
        retrieval_query = self._build_retrieval_query(
            question=question,
            history=history,
        )

        documents = self._retriever.retrieve(
            query=retrieval_query,
            top_k=top_k,
            document_id=document_id,
        )

        context = self._context_builder.build(documents)

        prompt = self._build_answer_prompt(
            question=question,
            context=context,
            history=history,
        )

        for chunk in self._llm_provider.stream(prompt):
            content = chunk.content
            if content:
                yield content

    def _build_retrieval_query(
        self,
        question: str,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        if not history:
            return question

        prompt = self._build_retrieval_query_prompt(
            question=question,
            history=history,
        )

        response = self._llm_provider.invoke(prompt)
        content = response.content

        if isinstance(content, str) and content.strip():
            return content.strip()

        return question

    def _generate_answer(
        self,
        question: str,
        context: str,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        prompt = self._build_answer_prompt(
            question=question,
            context=context,
            history=history,
        )

        response = self._llm_provider.invoke(prompt)
        content = response.content

        if isinstance(content, str):
            return content.strip()

        return str(content)

    def _build_retrieval_query_prompt(
        self,
        question: str,
        history: list[dict[str, str]],
    ) -> str:
        history_text = self._format_history(history)

        return f"""
Given the conversation history and the latest question, rewrite the latest
question as a standalone search query.

Preserve the user's intent and important entities.
Return only the standalone search query.

Conversation history:
{history_text}

Latest question:
{question}

Standalone search query:
""".strip()

    def _build_answer_prompt(
        self,
        question: str,
        context: str,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        history_text = self._format_history(history or [])

        return f"""
You are an enterprise document assistant.
Answer the user's question using the supplied document context.

Rules:
- Ground factual claims in the supplied context.
- If the context does not contain the answer, say so clearly.
- Do not invent facts.
- Use conversation history only to understand the user's intent.
- Keep the answer clear and relevant.

Conversation history:
{history_text}

Document context:
{context}

User question:
{question}

Answer:
""".strip()

    @staticmethod
    def _format_history(history: list[dict[str, str]]) -> str:
        if not history:
            return "No previous conversation."

        lines: list[str] = []

        for message in history:
            role = message.get("role", "user").strip().upper()
            content = message.get("content", "").strip()

            if content:
                lines.append(f"{role}: {content}")

        return "\n".join(lines) or "No previous conversation."
