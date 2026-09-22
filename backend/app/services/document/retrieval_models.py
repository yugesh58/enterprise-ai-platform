from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RetrievalResult:
    """
    Common representation for document retrieval results.

    Both semantic and keyword retrieval results are converted into
    this structure before hybrid ranking.
    """

    chunk_id: str
    document_id: str
    text: str
    source: str
    page_number: int
    chunk_index: int

    score: float
    retrieval_type: str

    metadata: dict[str, Any] | None = None