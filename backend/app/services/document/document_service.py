import hashlib
from uuid import UUID

from app.enums.document_status import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.storage.file_storage.base import FileStorageProvider


class DocumentService:
    """Manage document uploads with content-based deduplication."""

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
    ) -> dict:
        if not filename:
            raise ValueError("Filename cannot be empty.")

        if not content:
            raise ValueError("Document content cannot be empty.")

        if not content_type:
            raise ValueError("Content type cannot be empty.")

        content_hash = hashlib.sha256(content).hexdigest()

        # Reuse an existing document with identical content.
        existing = self._repository.get_by_content_hash(content_hash)

        if existing is not None:
            return self._handle_existing_document(existing)

        storage_path = self._storage.save(
            filename=filename,
            content=content,
        )

        try:
            document_id = self._repository.create(
                filename=filename,
                content_type=content_type,
                file_size=len(content),
                storage_path=str(storage_path),
                content_hash=content_hash,
            )

            return {
                "document_id": document_id,
                "status": DocumentStatus.PROCESSING.value,
                "is_existing": False,
                "should_index": True,
            }

        except Exception:
            # A concurrent request might have created the same hash.
            existing = self._repository.get_by_content_hash(content_hash)

            if existing is not None:
                self._storage.delete(storage_path)
                return self._handle_existing_document(existing)

            self._storage.delete(storage_path)
            raise

    def _handle_existing_document(self, document: dict) -> dict:
        document_id = document["id"]
        status = document["status"]

        status_value = (
            status.value if hasattr(status, "value") else str(status)
        )

        should_index = status_value == DocumentStatus.FAILED.value

        if should_index:
            self._repository.update_status(
                document_id,
                DocumentStatus.PROCESSING,
            )
            status_value = DocumentStatus.PROCESSING.value

        return {
            "document_id": document_id,
            "status": status_value,
            "is_existing": True,
            "should_index": should_index,
        }