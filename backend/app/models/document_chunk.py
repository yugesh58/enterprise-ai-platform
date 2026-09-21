from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.models.metadata import metadata


document_chunks = Table(
    "document_chunks",
    metadata,

    Column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
    ),

    Column(
        "document_id",
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    ),

    Column(
        "text",
        Text,
        nullable=False,
    ),

    Column(
        "source",
        String(255),
        nullable=False,
    ),

    Column(
        "page_number",
        Integer,
        nullable=False,
    ),

    Column(
        "chunk_index",
        Integer,
        nullable=False,
    ),

    Column(
        "created_at",
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    ),

    Index(
        "ix_document_chunks_document_id",
        "document_id",
    ),

    Index(
        "uq_document_chunks_document_chunk_index",
        "document_id",
        "chunk_index",
        unique=True,
    ),
)