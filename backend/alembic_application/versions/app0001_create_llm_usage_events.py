"""Create application LLM usage events table."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "app0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    runtime_user = op.get_context().config.attributes.get(
        "app_runtime_user"
    )
    if not runtime_user:
        raise RuntimeError(
            "APP_DATABASE_USER must be configured for the application migration."
        )

    op.create_table(
        "llm_usage_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("request_id", sa.String(length=100), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=150), nullable=False),
        sa.Column("operation", sa.String(length=30), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column(
            "estimated_cost_usd",
            sa.Numeric(precision=18, scale=10),
            nullable=True,
        ),
        sa.Column(
            "duration_ms",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column("outcome", sa.String(length=20), nullable=False),
        sa.Column("error_type", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    quoted_runtime_user = (
        op.get_bind().dialect.identifier_preparer.quote(runtime_user)
    )
    op.execute(
        f"GRANT SELECT, INSERT ON TABLE llm_usage_events "
        f"TO {quoted_runtime_user}"
    )

    op.create_index(
        "ix_llm_usage_events_created_at",
        "llm_usage_events",
        ["created_at"],
    )
    op.create_index(
        "ix_llm_usage_events_request_id",
        "llm_usage_events",
        ["request_id"],
    )
    op.create_index(
        "ix_llm_usage_events_provider_model",
        "llm_usage_events",
        ["provider", "model"],
    )


def downgrade() -> None:
    op.drop_table("llm_usage_events")
