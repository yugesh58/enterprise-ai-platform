"""initial schema

Revision ID: c89814a6158d
Revises: 
Create Date: 2026-07-20 22:40:50.899626

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c89814a6158d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "employee",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100)),
        sa.Column("email", sa.String(255), unique=True),
        sa.Column("department", sa.String(100)),
        sa.Column("salary", sa.Numeric(10, 2)),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def downgrade():
    op.drop_table("employee")
