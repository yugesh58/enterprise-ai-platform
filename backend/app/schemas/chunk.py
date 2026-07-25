from uuid import UUID

from pydantic import BaseModel


class ChunkMetadata(BaseModel):
    """Metadata associated with a chunk."""

    source: str
    page_number: int
    chunk_index: int


class DocumentChunk(BaseModel):
    """Represents a searchable document chunk."""

    chunk_id: str

    document_id: UUID

    text: str

    metadata: ChunkMetadata