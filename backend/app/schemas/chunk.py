from uuid import UUID

from pydantic import BaseModel


class ChunkMetadata(BaseModel):
    """Metadata associated with a document chunk."""

    source: str
    page_number: int
    chunk_index: int


class DocumentChunk(BaseModel):
    """Represents a searchable chunk."""

    document_id: UUID
    text: str
    metadata: ChunkMetadata