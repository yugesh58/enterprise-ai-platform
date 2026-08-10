from pydantic import BaseModel


from typing import Optional

class ChatRequest(BaseModel):
    question: str
    top_k: int = 5
    document_id: Optional[str] = None
