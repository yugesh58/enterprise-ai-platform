from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.engine import Connection

from app.enums.document_status import DocumentStatus
from app.models.document import documents


class DocumentRepository:
    """
    Repository responsible for CRUD operations on documents.
    """

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def create(
        self,
        filename: str,
        content_type: str,
        file_size: int,
        storage_path: str,
    ) -> UUID:
        """
        Create a new document record.

        Returns:
            UUID: ID of the newly created document.
        """

        statement = (
            insert(documents)
            .values(
                filename=filename,
                content_type=content_type,
                file_size=file_size,
                storage_path=storage_path,
            )
            .returning(documents.c.id)
        )

        result = self._connection.execute(statement)

        return result.scalar_one()

    def get_by_id(
        self,
        document_id: UUID,
    ) -> dict | None:
        """
        Retrieve a document by its ID.
        """

        statement = (
            select(documents)
            .where(documents.c.id == document_id)
        )

        result = self._connection.execute(statement)

        row = result.mappings().first()

        if row is None:
            return None

        return dict(row)

    def update_status(
        self,
        document_id: UUID,
        status: DocumentStatus,
    ) -> None:
        """
        Update the processing status of a document.
        """

        statement = (
            update(documents)
            .where(documents.c.id == document_id)
            .values(status=status)
        )

        self._connection.execute(statement)

    def delete(
        self,
        document_id: UUID,
    ) -> None:
        """
        Delete a document.
        """

        statement = (
            delete(documents)
            .where(documents.c.id == document_id)
        )

        self._connection.execute(statement)