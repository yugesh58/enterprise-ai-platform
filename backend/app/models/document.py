from sqlalchemy import (
    Table,
    Column,
    String,
    BigInteger,
    DateTime,
    text,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID

from app.models.metadata import metadata

from app.enums.document_status import DocumentStatus


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
)