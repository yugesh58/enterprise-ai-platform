from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.enums.document_status import DocumentStatus
from app.services.document.document_indexing_service import (
    DocumentIndexingService,
)

@pytest.fixture(autouse=True)
def bypass_redis_lock(monkeypatch):
    monkeypatch.setattr(
        "app.services.document.document_indexing_service.document_index_lock",
        lambda document_id: nullcontext(),
    )
@pytest.fixture
def indexing_dependencies():
    document_id = uuid4()

    repository = Mock()
    repository.get_by_id.return_value = {
        "id": document_id,
        "filename": "test.pdf",
        "storage_path": "/tmp/test.pdf",
    }

    chunk_repository = Mock()
    chunk_repository.get_by_document_id.return_value = []
    chunk_repository.get_ids_by_document_id.return_value = []

    storage = Mock()
    storage.read.return_value = b"fake-pdf-content"

    pdf_processor = Mock()
    pdf_processor.extract_document.return_value = SimpleNamespace(
        pages=[SimpleNamespace()]
    )

    chunking_service = Mock()
    vector_provider = Mock()

    return {
        "document_id": document_id,
        "repository": repository,
        "chunk_repository": chunk_repository,
        "storage": storage,
        "pdf_processor": pdf_processor,
        "chunking_service": chunking_service,
        "vector_provider": vector_provider,
    }


def build_service(deps):
    return DocumentIndexingService(
        repository=deps["repository"],
        chunk_repository=deps["chunk_repository"],
        storage=deps["storage"],
        pdf_processing_service=deps["pdf_processor"],
        chunking_service=deps["chunking_service"],
        vector_provider=deps["vector_provider"],
    )


def test_indexing_marks_missing_document_as_error(indexing_dependencies):
    deps = indexing_dependencies
    deps["repository"].get_by_id.return_value = None

    service = build_service(deps)

    with pytest.raises(ValueError, match="not found"):
        service.index_document(deps["document_id"])

    deps["repository"].update_status.assert_not_called()


def test_indexing_marks_document_failed_when_storage_read_fails(
    indexing_dependencies,
):
    deps = indexing_dependencies
    deps["storage"].read.side_effect = OSError("Storage unavailable")

    with patch(
        "app.services.document.document_indexing_service.get_embeddings"
    ) as get_embeddings:
        get_embeddings.return_value = Mock()
        service = build_service(deps)

        with pytest.raises(OSError, match="Storage unavailable"):
            service.index_document(deps["document_id"])

    statuses = [
        call.args[1]
        for call in deps["repository"].update_status.call_args_list
    ]

    assert statuses == [
        DocumentStatus.PROCESSING,
        DocumentStatus.FAILED,
    ]


def test_indexing_marks_empty_document_as_indexed(indexing_dependencies):
    deps = indexing_dependencies
    deps["chunking_service"].chunk_document.return_value = []

    with patch(
        "app.services.document.document_indexing_service.get_embeddings"
    ) as get_embeddings:
        get_embeddings.return_value = Mock()

        service = build_service(deps)
        service.index_document(deps["document_id"])

    deps["chunk_repository"].replace_by_document_id.assert_called_once_with(
        deps["document_id"],
        [],
    )

    deps["vector_provider"].upsert.assert_not_called()

    deps["vector_provider"].delete.assert_called_once_with(
        collection_name=pytest.importorskip(
            "app.core.config"
        ).settings.QDRANT_COLLECTION,
        point_ids=[],
    )

    deps["repository"].update_status.assert_any_call(
        deps["document_id"],
        DocumentStatus.INDEXED,
    )


def test_successful_indexing_persists_chunks_and_vectors(
    indexing_dependencies,
):
    from app.schemas.embedding import ChunkMetadata

    deps = indexing_dependencies
    document_id = deps["document_id"]
    chunk_id = uuid4()

    chunk = SimpleNamespace(
        chunk_id=chunk_id,
        document_id=document_id,
        text="Enterprise AI uses a Document Agent.",
        metadata=ChunkMetadata(
            source="test.pdf",
            page_number=1,
            chunk_index=0,
        ),
    )

    deps["chunking_service"].chunk_document.return_value = [chunk]

    embeddings = Mock()
    embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3]]

    vector_points = [
        SimpleNamespace(id="vector-point-1")
    ]

    with (
        patch(
            "app.services.document.document_indexing_service.get_embeddings",
            return_value=embeddings,
        ),
        patch(
            "app.services.document.document_indexing_service.VectorMapper.to_vector_points",
            return_value=vector_points,
        ) as map_vectors,
    ):
        service = build_service(deps)
        service.index_document(document_id)

    embeddings.embed_documents.assert_called_once_with(
        ["Enterprise AI uses a Document Agent."]
    )

    map_vectors.assert_called_once()

    deps["vector_provider"].upsert.assert_called_once_with(
        collection_name=pytest.importorskip(
            "app.core.config"
        ).settings.QDRANT_COLLECTION,
        points=vector_points,
    )

    deps["chunk_repository"].replace_by_document_id.assert_called_once_with(
        document_id,
        [
            {
                "id": chunk_id,
                "document_id": document_id,
                "text": "Enterprise AI uses a Document Agent.",
                "source": "test.pdf",
                "page_number": 1,
                "chunk_index": 0,
            }
        ],
    )

    deps["chunk_repository"].create_many.assert_not_called()
    deps["chunk_repository"].delete_by_document_id.assert_not_called()

    deps["vector_provider"].delete_by_filter.assert_not_called()

    deps["repository"].update_status.assert_any_call(
        document_id,
        DocumentStatus.INDEXED,
    )


def test_indexing_marks_document_failed_when_embedding_fails(
    indexing_dependencies,
):
    from app.schemas.chunk import ChunkMetadata

    deps = indexing_dependencies

    chunk = SimpleNamespace(
        chunk_id=uuid4(),
        document_id=deps["document_id"],
        text="Test document content",
        metadata=ChunkMetadata(
            source="test.pdf",
            page_number=1,
            chunk_index=0,
        ),
    )

    deps["chunking_service"].chunk_document.return_value = [chunk]

    embeddings = Mock()
    embeddings.embed_documents.side_effect = RuntimeError(
        "Embedding generation failed"
    )

    with patch(
        "app.services.document.document_indexing_service.get_embeddings",
        return_value=embeddings,
    ):
        service = build_service(deps)

        with pytest.raises(
            RuntimeError,
            match="Embedding generation failed",
        ):
            service.index_document(deps["document_id"])

    deps["repository"].update_status.assert_any_call(
        deps["document_id"],
        DocumentStatus.FAILED,
    )

    deps["vector_provider"].upsert.assert_not_called()


def test_indexing_marks_document_failed_when_qdrant_upsert_fails(
    indexing_dependencies,
):
    from app.schemas.chunk import ChunkMetadata

    deps = indexing_dependencies

    chunk = SimpleNamespace(
        chunk_id=uuid4(),
        document_id=deps["document_id"],
        text="Test document content",
        metadata=ChunkMetadata(
            source="test.pdf",
            page_number=1,
            chunk_index=0,
        ),
    )

    deps["chunking_service"].chunk_document.return_value = [chunk]

    embeddings = Mock()
    embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3]]

    deps["vector_provider"].upsert.side_effect = RuntimeError(
        "Qdrant unavailable"
    )

    vector_points = [
        SimpleNamespace(id="vector-point-1")
    ]

    with (
        patch(
            "app.services.document.document_indexing_service.get_embeddings",
            return_value=embeddings,
        ),
        patch(
            "app.services.document.document_indexing_service.VectorMapper.to_vector_points",
            return_value=vector_points,
        ),
    ):
        service = build_service(deps)

        with pytest.raises(
            RuntimeError,
            match="Qdrant unavailable",
        ):
            service.index_document(deps["document_id"])

    # New vector IDs are compensated even if upsert raises.
    deps["vector_provider"].delete.assert_called_once_with(
        collection_name=pytest.importorskip(
            "app.core.config"
        ).settings.QDRANT_COLLECTION,
        point_ids=["vector-point-1"],
    )

    # PostgreSQL must not be replaced after a failed upsert.
    deps["chunk_repository"].replace_by_document_id.assert_not_called()

    deps["repository"].update_status.assert_any_call(
        deps["document_id"],
        DocumentStatus.FAILED,
    )


def test_indexing_replaces_existing_chunks(
    indexing_dependencies,
):
    from app.schemas.chunk import ChunkMetadata

    deps = indexing_dependencies
    document_id = deps["document_id"]

    old_chunk_id = uuid4()

    deps["chunk_repository"].get_ids_by_document_id.return_value = [
        old_chunk_id
    ]

    new_chunk = SimpleNamespace(
        chunk_id=uuid4(),
        document_id=document_id,
        text="Replacement chunk",
        metadata=ChunkMetadata(
            source="test.pdf",
            page_number=1,
            chunk_index=0,
        ),
    )

    deps["chunking_service"].chunk_document.return_value = [new_chunk]

    embeddings = Mock()
    embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3]]

    vector_points = [
        SimpleNamespace(id="replacement-vector")
    ]

    with (
        patch(
            "app.services.document.document_indexing_service.get_embeddings",
            return_value=embeddings,
        ),
        patch(
            "app.services.document.document_indexing_service.VectorMapper.to_vector_points",
            return_value=vector_points,
        ),
    ):
        service = build_service(deps)
        service.index_document(document_id)

    deps["chunk_repository"].replace_by_document_id.assert_called_once_with(
        document_id,
        [
            {
                "id": new_chunk.chunk_id,
                "document_id": document_id,
                "text": "Replacement chunk",
                "source": "test.pdf",
                "page_number": 1,
                "chunk_index": 0,
            }
        ],
    )

    # Old vectors are deleted by their exact IDs.
    deps["vector_provider"].delete.assert_called_once_with(
        collection_name=pytest.importorskip(
            "app.core.config"
        ).settings.QDRANT_COLLECTION,
        point_ids=[str(old_chunk_id)],
    )

    deps["vector_provider"].delete_by_filter.assert_not_called()

    deps["chunk_repository"].delete_by_document_id.assert_not_called()
    deps["chunk_repository"].create_many.assert_not_called()

    deps["vector_provider"].upsert.assert_called_once_with(
        collection_name=pytest.importorskip(
            "app.core.config"
        ).settings.QDRANT_COLLECTION,
        points=vector_points,
    )

    deps["repository"].update_status.assert_any_call(
        document_id,
        DocumentStatus.INDEXED,
    )

def test_indexing_compensates_when_postgres_replacement_fails(
    indexing_dependencies,
):
    from app.schemas.chunk import ChunkMetadata

    deps = indexing_dependencies
    document_id = deps["document_id"]

    old_chunk_id = uuid4()
    deps["chunk_repository"].get_ids_by_document_id.return_value = [
        old_chunk_id
    ]

    chunk = SimpleNamespace(
        chunk_id=uuid4(),
        document_id=document_id,
        text="Replacement chunk",
        metadata=ChunkMetadata(
            source="test.pdf",
            page_number=1,
            chunk_index=0,
        ),
    )

    deps["chunking_service"].chunk_document.return_value = [chunk]

    embeddings = Mock()
    embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3]]

    deps["chunk_repository"].replace_by_document_id.side_effect = (
        RuntimeError("PostgreSQL replacement failed")
    )

    vector_points = [
        SimpleNamespace(id="new-vector-123")
    ]

    with (
        patch(
            "app.services.document.document_indexing_service.get_embeddings",
            return_value=embeddings,
        ),
        patch(
            "app.services.document.document_indexing_service.VectorMapper.to_vector_points",
            return_value=vector_points,
        ),
    ):
        service = build_service(deps)

        with pytest.raises(
            RuntimeError,
            match="PostgreSQL replacement failed",
        ):
            service.index_document(document_id)

    # New vectors were uploaded before PostgreSQL replacement.
    deps["vector_provider"].upsert.assert_called_once()

    # PostgreSQL replacement was attempted.
    deps["chunk_repository"].replace_by_document_id.assert_called_once()

    # Newly uploaded vectors must be removed.
    deps["vector_provider"].delete.assert_called_once_with(
        collection_name=__import__(
            "app.core.config",
            fromlist=["settings"],
        ).settings.QDRANT_COLLECTION,
        point_ids=["new-vector-123"],
    )

    # Old vectors must not be deleted.
    deps["vector_provider"].delete_by_filter.assert_not_called()

    # Document must be marked failed.
    deps["repository"].update_status.assert_any_call(
        document_id,
        DocumentStatus.FAILED,
    )

def test_indexing_remains_indexed_when_old_vector_cleanup_fails(
    indexing_dependencies,
):
    from app.schemas.chunk import ChunkMetadata

    deps = indexing_dependencies
    document_id = deps["document_id"]

    old_chunk_id = uuid4()
    deps["chunk_repository"].get_ids_by_document_id.return_value = [
        old_chunk_id
    ]

    chunk = SimpleNamespace(
        chunk_id=uuid4(),
        document_id=document_id,
        text="Replacement chunk",
        metadata=ChunkMetadata(
            source="test.pdf",
            page_number=1,
            chunk_index=0,
        ),
    )

    deps["chunking_service"].chunk_document.return_value = [chunk]

    embeddings = Mock()
    embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3]]

    deps["vector_provider"].delete.side_effect = RuntimeError(
        "Old vector cleanup failed"
    )

    vector_points = [
        SimpleNamespace(id="new-vector-123")
    ]

    with (
        patch(
            "app.services.document.document_indexing_service.get_embeddings",
            return_value=embeddings,
        ),
        patch(
            "app.services.document.document_indexing_service.VectorMapper.to_vector_points",
            return_value=vector_points,
        ),
    ):
        service = build_service(deps)
        service.index_document(document_id)

    # New vectors were uploaded.
    deps["vector_provider"].upsert.assert_called_once()

    # PostgreSQL replacement succeeded.
    deps["chunk_repository"].replace_by_document_id.assert_called_once()

    # Cleanup was attempted for the old vector IDs.
    deps["vector_provider"].delete.assert_called_once()
    assert deps["vector_provider"].delete.call_args.kwargs["point_ids"] == [
        str(old_chunk_id)
    ]

    # Cleanup failure must not mark the document as failed.
    deps["repository"].update_status.assert_any_call(
        document_id,
        DocumentStatus.INDEXED,
    )

    statuses = [
    call.args[1]
    for call in deps["repository"].update_status.call_args_list
    ]

    assert DocumentStatus.INDEXED in statuses
    assert DocumentStatus.FAILED not in statuses

def test_empty_reindex_clears_existing_chunks_and_vectors(
    indexing_dependencies,
):
    deps = indexing_dependencies
    document_id = deps["document_id"]

    old_chunk_ids = [uuid4(), uuid4()]

    deps["chunk_repository"].get_ids_by_document_id.return_value = (
        old_chunk_ids
    )
    deps["chunking_service"].chunk_document.return_value = []

    service = build_service(deps)
    service.index_document(document_id)

    deps["chunk_repository"].replace_by_document_id.assert_called_once_with(
        document_id,
        [],
    )

    deps["vector_provider"].delete.assert_called_once_with(
        collection_name=__import__(
            "app.core.config",
            fromlist=["settings"],
        ).settings.QDRANT_COLLECTION,
        point_ids=[str(chunk_id) for chunk_id in old_chunk_ids],
    )

    statuses = [
        call.args[1]
        for call in deps["repository"].update_status.call_args_list
    ]

    assert DocumentStatus.INDEXED in statuses
    assert DocumentStatus.FAILED not in statuses
