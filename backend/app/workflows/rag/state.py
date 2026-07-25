from langchain_core.documents import Document
from typing_extensions import TypedDict


class RAGState(TypedDict):
    question: str

    documents: list[Document]

    answer: str

    sources: list[str]
