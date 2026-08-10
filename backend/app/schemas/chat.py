from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    top_k: int = 5
    document_id: Optional[str] = None


class SourceChunk(BaseModel):
    source: str
    page_number: int
    score: float
    text: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]