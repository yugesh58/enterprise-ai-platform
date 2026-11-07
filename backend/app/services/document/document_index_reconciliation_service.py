from uuid import UUID

from app.core.config import settings
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.storage.vectorstore.base import VectorProvider


class DocumentIndexReconciliationService:
    """Compare PostgreSQL document chunks with Qdrant vectors."""

    def __init__(
        self,
        chunk_repository: DocumentChunkRepository,
        vector_provider: VectorProvider,
        collection_name: str | None = None,
        page_size: int = 500,
    ) -> None:
        if page_size <= 0:
            raise ValueError("page_size must be greater than zero.")

        self._chunk_repository = chunk_repository
        self._vector_provider = vector_provider
        self._collection_name = (
            collection_name or settings.QDRANT_COLLECTION
        )
        self._page_size = page_size

    def reconcile(self) -> dict:
        """Return discrepancies without modifying either data store."""

        postgres_ids = self._get_postgres_ids()
        qdrant_ids = self._get_qdrant_ids()

        missing_vector_ids = sorted(postgres_ids - qdrant_ids)
        orphan_vector_ids = sorted(qdrant_ids - postgres_ids)

        return {
            "postgres_chunk_count": len(postgres_ids),
            "qdrant_vector_count": len(qdrant_ids),
            "missing_vector_ids": missing_vector_ids,
            "orphan_vector_ids": orphan_vector_ids,
            "is_consistent": not (
                missing_vector_ids or orphan_vector_ids
            ),
        }

    def _get_postgres_ids(self) -> set[str]:
        chunk_ids: set[str] = set()
        after_id: UUID | None = None

        while True:
            page = self._chunk_repository.get_ids_page(
                limit=self._page_size,
                after_id=after_id,
            )

            if not page:
                break

            chunk_ids.update(str(chunk_id) for chunk_id in page)
            after_id = page[-1]

        return chunk_ids

    def _get_qdrant_ids(self) -> set[str]:
        vector_ids: set[str] = set()
        offset: str | int | None = None
        seen_offsets: set[str | int] = set()

        while True:
            points, next_offset = self._vector_provider.scroll(
                collection_name=self._collection_name,
                limit=self._page_size,
                offset=offset,
            )

            vector_ids.update(
                str(point["id"]) for point in points
            )

            if next_offset is None:
                break

            if next_offset == offset or next_offset in seen_offsets:
                raise RuntimeError(
                    "Qdrant scroll returned a repeated pagination cursor."
                )

            seen_offsets.add(next_offset)
            offset = next_offset

        return vector_ids