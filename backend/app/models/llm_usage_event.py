from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.models.metadata import metadata


llm_usage_events = Table(
    "llm_usage_events",
    metadata,

    Column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    ),

    Column("request_id", String(100), nullable=True),
    Column("provider", String(50), nullable=False),
    Column("model", String(150), nullable=False),
    Column("operation", String(30), nullable=False),

    Column("input_tokens", Integer, nullable=True),
    Column("output_tokens", Integer, nullable=True),
    Column("total_tokens", Integer, nullable=True),

    Column("estimated_cost_usd", Numeric(18, 10), nullable=True),
    Column("duration_ms", Numeric(12, 2), nullable=False),
    Column("outcome", String(20), nullable=False),

    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    ),

    Index("ix_llm_usage_events_created_at", "created_at"),
    Index("ix_llm_usage_events_request_id", "request_id"),
    Index("ix_llm_usage_events_provider_model", "provider", "model"),
)