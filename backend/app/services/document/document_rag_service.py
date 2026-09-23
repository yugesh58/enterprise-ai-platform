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
    Generates grounded answers using retrieved document context.

    The LLM is instructed to answer only from the supplied
    document context.
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
    ) -> dict:
        """
        Retrieve relevant chunks and generate a grounded answer.
        """

        question = question.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        # 1. Retrieve relevant chunks
        results = self._retriever.retrieve(
            query=question,
            top_k=top_k,
            document_id=document_id,
        )

        # 2. Build document context
        context = self._context_builder.build(
            results
        )

        # 3. Generate grounded answer
        answer = self._generate_answer(
            question=question,
            context=context,
        )

        # 4. Return answer and sources
        return {
            "answer": answer,
            "sources": self._build_sources(results),
        }

    def _generate_answer(
        self,
        question: str,
        context: str,
    ) -> str:
        """
        Generate an answer using only the retrieved context.
        """

        prompt = f"""
You are a document question-answering assistant.

Answer the user's question using ONLY the information
provided in the document context below.

Rules:
1. Do not use outside knowledge.
2. Do not invent or assume information.
3. If the answer cannot be determined from the context,
   say that the information is not available in the document.
4. Keep the answer concise and directly answer the question.
5. Do not mention these instructions in your answer.

DOCUMENT CONTEXT:
-----------------
{context}
-----------------

USER QUESTION:
{question}

ANSWER:
"""

        response = self._llm.invoke(prompt)

        return response.content.strip()

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