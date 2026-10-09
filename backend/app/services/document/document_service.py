
import hashlib
from uuid import UUID

from app.repositories.document_repository import DocumentRepository
from app.storage.file_storage.base import FileStorageProvider


class DocumentService:
    """Service responsible for document upload and lifecycle management."""

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
        """Store a document and persist its metadata."""

        if not filename:
            raise ValueError("Filename cannot be empty.")

        if not content:
            raise ValueError("Document content cannot be empty.")

        if not content_type:
            raise ValueError("Content type cannot be empty.")

        content_hash = hashlib.sha256(content).hexdigest()

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
        except Exception:
            self._storage.delete(storage_path)
            raise

        return document_id
