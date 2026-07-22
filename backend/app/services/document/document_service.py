from uuid import UUID

from app.repositories.document_repository import DocumentRepository
from app.storage.file_storage.base import FileStorageProvider


class DocumentService:
    """
    Service responsible for document upload and lifecycle management.
    """

    def __init__(
        self,
        repository: DocumentRepository,
        storage: FileStorageProvider,
    ) -> None:
        self._repository = repository
        self._storage = storage

    def upload_document(
        self,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> UUID:
        """
        Upload a document by saving it to storage and creating
        its metadata record in the database.

        Args:
            filename: Name of the uploaded file.
            content_type: MIME type of the uploaded file.
            content: Binary content of the file.

        Returns:
            UUID: Identifier of the created document.

        Raises:
            ValueError: If any required input is missing.
            Exception: Re-raises any storage or database exception after cleanup.
        """

        # Validate inputs
        if not filename:
            raise ValueError("Filename cannot be empty.")

        if not content:
            raise ValueError("Document content cannot be empty.")

        if not content_type:
            raise ValueError("Content type cannot be empty.")

        # Save file to storage
        storage_path = self._storage.save(
            filename=filename,
            content=content,
        )

        try:
            # Persist document metadata
            document_id = self._repository.create(
                filename=filename,
                content_type=content_type,
                file_size=len(content),
                storage_path=str(storage_path),
            )
        except Exception:
            # Cleanup file if database operation fails
            self._storage.delete(storage_path)
            raise

        return document_id