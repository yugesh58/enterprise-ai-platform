from typing_extensions import TypedDict
from langchain_core.documents import Document


class RAGState(TypedDict):
    question: str

    documents: list[Document]

    answer: str

    sources: list[str]