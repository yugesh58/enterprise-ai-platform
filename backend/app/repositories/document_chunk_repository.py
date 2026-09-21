from uuid import UUID

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from app.models.document_chunk import document_chunks


class DocumentChunkRepository:
    """
    Repository responsible for CRUD and search operations on document chunks.
    """

    def __init__(self, connection: Session) -> None:
        self._connection = connection

    def create_many(
        self,
        chunks: list[dict],
    ) -> None:
        """
        Create multiple document chunk records.
        """

        if not chunks:
            return

        statement = insert(document_chunks).values(chunks)

        self._connection.execute(statement)
        self._connection.commit()

    def get_by_document_id(
        self,
        document_id: UUID,
    ) -> list[dict]:
        """
        Return all chunks belonging to a document.
        """

        statement = (
            select(document_chunks)
            .where(document_chunks.c.document_id == document_id)
            .order_by(document_chunks.c.chunk_index)
        )

        result = self._connection.execute(statement)

        return [dict(row) for row in result.mappings().all()]

    def get_ids_by_document_id(
        self,
        document_id: UUID,
    ) -> list[UUID]:
        """
        Return the IDs of all chunks belonging to a document.
        """

        statement = (
            select(document_chunks.c.id)
            .where(document_chunks.c.document_id == document_id)
            .order_by(document_chunks.c.chunk_index)
        )

        result = self._connection.execute(statement)

        return list(result.scalars().all())

    def delete_by_document_id(
        self,
        document_id: UUID,
    ) -> None:
        """
        Delete all chunks belonging to a document.
        """

        statement = (
            delete(document_chunks)
            .where(document_chunks.c.document_id == document_id)
        )

        self._connection.execute(statement)
        self._connection.commit()