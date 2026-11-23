
from uuid import UUID

from sqlalchemy import delete, func, insert, select, text, update
from sqlalchemy.orm import Session

from app.enums.document_status import DocumentStatus
from app.models.document import documents


class DocumentRepository:
    """Repository responsible for CRUD operations on documents."""

    def __init__(self, connection: Session) -> None:
        self._connection = connection

    def create(
        self,
        filename: str,
        content_type: str,
        file_size: int,
        storage_path: str,
        content_hash: str,
    ) -> UUID:
        """Create a new document record."""

        statement = (
            insert(documents)
            .values(
                filename=filename,
                content_type=content_type,
                file_size=file_size,
                storage_path=storage_path,
                content_hash=content_hash,
            )
            .returning(documents.c.id)
        )

        try:
            result = self._connection.execute(statement)
            document_id = result.scalar_one()
            self._connection.commit()
            return document_id
        except Exception:
            self._connection.rollback()
            raise

    def get_by_id(self, document_id: UUID) -> dict | None:
        statement = (
            select(documents)
            .where(documents.c.id == document_id)
        )

        result = self._connection.execute(statement)
        row = result.mappings().first()

        return dict(row) if row is not None else None

    def update_status(
        self,
        document_id: UUID,
        status: DocumentStatus,
    ) -> None:
        statement = (
            update(documents)
            .where(documents.c.id == document_id)
            .values(
                status=status,
                updated_at=func.now(),
            )
        )

        try:
            self._connection.execute(statement)
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def get_stale_processing_ids(
        self,
        timeout_seconds: int,
    ) -> list[UUID]:
        """Return IDs of processing documents older than the timeout."""

        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")

        stale_before = (
            func.now() - text("(:timeout_seconds * INTERVAL '1 second')").bindparams(
                timeout_seconds=timeout_seconds
            )
        )

        statement = (
            select(documents.c.id)
            .where(
                documents.c.status == DocumentStatus.PROCESSING,
                documents.c.updated_at < stale_before,
            )
            .order_by(documents.c.updated_at.asc())
        )

        result = self._connection.execute(statement)
        return list(result.scalars().all())

    def mark_failed_if_stale(
        self,
        document_id: UUID,
        timeout_seconds: int,
    ) -> bool:
        """Atomically fail a document only if it remains stale."""

        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")

        stale_before = (
            func.now() - text("(:timeout_seconds * INTERVAL '1 second')").bindparams(
                timeout_seconds=timeout_seconds
            )
        )

        statement = (
            update(documents)
            .where(
                documents.c.id == document_id,
                documents.c.status == DocumentStatus.PROCESSING,
                documents.c.updated_at < stale_before,
            )
            .values(
                status=DocumentStatus.FAILED,
                updated_at=func.now(),
            )
        )

        try:
            result = self._connection.execute(statement)
            self._connection.commit()
            return result.rowcount == 1
        except Exception:
            self._connection.rollback()
            raise

    def delete(self, document_id: UUID) -> None:
        statement = (
            delete(documents)
            .where(documents.c.id == document_id)
        )

        try:
            self._connection.execute(statement)
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise
    def get_by_content_hash(self, content_hash: str) -> dict | None:
        statement = (
            select(documents)
            .where(documents.c.content_hash == content_hash)
        )

        result = self._connection.execute(statement)
        row = result.mappings().first()

        return dict(row) if row is not None else None
