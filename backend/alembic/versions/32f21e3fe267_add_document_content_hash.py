"""add document content hash

Revision ID: 32f21e3fe267
Revises: 2ba43737f262
Create Date: 2026-08-10 21:03:56.747285
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "32f21e3fe267"
down_revision: Union[str, Sequence[str], None] = "2ba43737f262"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "content_hash",
            sa.String(length=64),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "documents",
        "content_hash",
    )