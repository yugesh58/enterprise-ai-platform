from uuid import UUID

from pydantic import BaseModel

from app.schemas.chunk import ChunkMetadata


class EmbeddedChunk(BaseModel):
    """
    Represents a document chunk together with its embedding vector.
    """

    chunk_id: UUID
    document_id: UUID
    text: str
    embedding: list[float]
    metadata: ChunkMetadata