from alembic import op
import sqlalchemy as sa


revision = "bbcc1ec534af"
down_revision = "36c6ebdbc1b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_document_chunks_text_search",
        "document_chunks",
        [sa.text("to_tsvector('english', text)")],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_chunks_text_search",
        table_name="document_chunks",
    )