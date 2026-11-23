from app.core.config import settings
from app.repositories.document_repository import DocumentRepository
from app.services.document.document_index_lock import (
    DocumentIndexingAlreadyInProgress,
    document_index_lock,
)


class DocumentIndexRecoveryService:
    """Recover document indexing jobs abandoned by terminated workers."""

    def __init__(
        self,
        repository: DocumentRepository,
        stale_timeout_seconds: int | None = None,
    ) -> None:
        self._repository = repository
        self._stale_timeout_seconds = (
            stale_timeout_seconds
            if stale_timeout_seconds is not None
            else settings.DOCUMENT_INDEXING_STALE_TIMEOUT_SECONDS
        )

        if self._stale_timeout_seconds <= 0:
            raise ValueError(
                "stale_timeout_seconds must be greater than zero."
            )

    def recover_stale_documents(self) -> dict:
        """Mark abandoned indexing jobs as failed without interrupting active jobs."""

        stale_document_ids = self._repository.get_stale_processing_ids(
            self._stale_timeout_seconds
        )

        recovered = []
        skipped = []

        for document_id in stale_document_ids:
            try:
                with document_index_lock(document_id):
                    marked_failed = self._repository.mark_failed_if_stale(
                        document_id,
                        self._stale_timeout_seconds,
                    )

                if marked_failed:
                    recovered.append(str(document_id))
                else:
                    skipped.append(str(document_id))

            except DocumentIndexingAlreadyInProgress:
                skipped.append(str(document_id))

        return {
            "scanned": len(stale_document_ids),
            "recovered": len(recovered),
            "skipped": len(skipped),
            "recovered_document_ids": recovered,
            "skipped_document_ids": skipped,
        }
