from uuid import uuid4

import pytest

from app.services.document.document_index_reconciliation_service import (
    DocumentIndexReconciliationService,
)


class FakeChunkRepository:
    def __init__(self, chunk_ids, page_size=2):
        self.chunk_ids = sorted(chunk_ids)
        self.page_size = page_size
        self.calls = []

    def get_ids_page(self, limit=500, after_id=None):
        self.calls.append(after_id)

        remaining = [
            chunk_id
            for chunk_id in self.chunk_ids
            if after_id is None or chunk_id > after_id
        ]

        return remaining[:limit]


class FakeVectorProvider:
    def __init__(self, point_ids, page_size=2):
        self.point_ids = sorted(str(point_id) for point_id in point_ids)
        self.page_size = page_size
        self.calls = []

    def scroll(self, collection_name, limit=256, offset=None):
        self.calls.append((collection_name, offset))

        start = int(offset or 0)
        page = self.point_ids[start:start + limit]
        next_offset = start + len(page)

        if next_offset >= len(self.point_ids):
            next_offset = None

        return (
            [{"id": point_id, "payload": {}} for point_id in page],
            next_offset,
        )


def create_service(chunk_ids, vector_ids, page_size=2):
    repository = FakeChunkRepository(chunk_ids)
    vector_provider = FakeVectorProvider(vector_ids)

    service = DocumentIndexReconciliationService(
        chunk_repository=repository,
        vector_provider=vector_provider,
        collection_name="test_collection",
        page_size=page_size,
    )

    return service, repository, vector_provider


def test_reconciliation_reports_consistent_stores():
    chunk_ids = [uuid4(), uuid4(), uuid4()]

    service, _, _ = create_service(
        chunk_ids,
        [str(chunk_id) for chunk_id in chunk_ids],
    )

    report = service.reconcile()

    assert report["is_consistent"] is True
    assert report["postgres_chunk_count"] == 3
    assert report["qdrant_vector_count"] == 3
    assert report["missing_vector_ids"] == []
    assert report["orphan_vector_ids"] == []


def test_reconciliation_detects_missing_vectors():
    chunk_ids = [uuid4(), uuid4()]

    service, _, _ = create_service(
        chunk_ids,
        [str(chunk_ids[0])],
    )

    report = service.reconcile()

    assert report["is_consistent"] is False
    assert report["missing_vector_ids"] == [str(chunk_ids[1])]
    assert report["orphan_vector_ids"] == []


def test_reconciliation_detects_orphan_vectors():
    chunk_id = uuid4()
    orphan_id = uuid4()

    service, _, _ = create_service(
        [chunk_id],
        [str(chunk_id), str(orphan_id)],
    )

    report = service.reconcile()

    assert report["is_consistent"] is False
    assert report["missing_vector_ids"] == []
    assert report["orphan_vector_ids"] == [str(orphan_id)]


def test_reconciliation_handles_empty_stores():
    service, _, _ = create_service([], [])

    report = service.reconcile()

    assert report["is_consistent"] is True
    assert report["postgres_chunk_count"] == 0
    assert report["qdrant_vector_count"] == 0


def test_reconciliation_uses_pagination():
    chunk_ids = [uuid4() for _ in range(5)]

    service, repository, vector_provider = create_service(
        chunk_ids,
        [str(chunk_id) for chunk_id in chunk_ids],
        page_size=2,
    )

    report = service.reconcile()

    assert report["is_consistent"] is True
    assert len(repository.calls) >= 3
    assert len(vector_provider.calls) >= 3
    assert all(
        call[0] == "test_collection"
        for call in vector_provider.calls
    )


def test_reconciliation_rejects_invalid_page_size():
    with pytest.raises(ValueError, match="page_size must be greater than zero"):
        DocumentIndexReconciliationService(
            chunk_repository=FakeChunkRepository([]),
            vector_provider=FakeVectorProvider([]),
            page_size=0,
        )


def test_reconciliation_detects_repeated_qdrant_cursor():
    class RepeatingCursorProvider:
        def scroll(self, collection_name, limit=256, offset=None):
            return [{"id": "vector-1"}], 1

    service = DocumentIndexReconciliationService(
        chunk_repository=FakeChunkRepository([]),
        vector_provider=RepeatingCursorProvider(),
        page_size=2,
    )

    with pytest.raises(RuntimeError, match="repeated pagination cursor"):
        service.reconcile()