from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import Session

from app.enums.document_status import DocumentStatus
from app.models.document import documents


class DocumentRepository:
    """
    Repository responsible for CRUD operations on documents.
    """

    def __init__(self, connection: Session) -> None:
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
        """

        print("\n" + "=" * 80)
        print("DOCUMENT CREATE")
        print("=" * 80)
        print(f"Database : {self._connection.bind.url}")
        print(f"Filename : {filename}")
        print(f"Storage  : {storage_path}")

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

        document_id = result.scalar_one()

        print(f"Generated ID : {document_id}")

        self._connection.commit()

        print("✅ INSERT COMMITTED")

        return document_id

    def get_by_id(
        self,
        document_id: UUID,
    ) -> dict | None:

        print(f"\nLooking for document: {document_id}")

        statement = (
            select(documents)
            .where(documents.c.id == document_id)
        )

        result = self._connection.execute(statement)

        row = result.mappings().first()

        if row is None:
            print("❌ Document NOT FOUND")
            return None

        print("✅ Document FOUND")

        return dict(row)

    def update_status(
        self,
        document_id: UUID,
        status: DocumentStatus,
    ) -> None:

        print(f"\nUpdating status -> {status}")

        statement = (
            update(documents)
            .where(documents.c.id == document_id)
            .values(status=status)
        )

        self._connection.execute(statement)
        self._connection.commit()

        print("✅ STATUS UPDATED")

    def delete(
        self,
        document_id: UUID,
    ) -> None:

        print(f"\nDeleting document: {document_id}")

        statement = (
            delete(documents)
            .where(documents.c.id == document_id)
        )

        self._connection.execute(statement)
        self._connection.commit()

        print("✅ DELETE COMMITTED")