from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    Index,
    String,
    Table,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.enums.document_status import DocumentStatus
from app.models.metadata import metadata


documents = Table(
    "documents",
    metadata,

    Column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    ),

    Column(
        "filename",
        String(255),
        nullable=False,
    ),

    Column(
        "content_type",
        String(100),
        nullable=False,
    ),

    Column(
        "file_size",
        BigInteger,
        nullable=False,
    ),

    Column(
        "storage_path",
        String(1000),
        nullable=False,
    ),

    Column(
        "content_hash",
        String(64),
        nullable=False,
    ),

    Column(
        "status",
        Enum(
            DocumentStatus,
            name="document_status",
        ),
        nullable=False,
        server_default=DocumentStatus.UPLOADED.value,
    ),

    Column(
        "created_at",
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    ),

    Column(
        "updated_at",
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    ),

    Index(
        "uq_documents_content_hash",
        "content_hash",
        unique=True,
    ),
)