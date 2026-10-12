
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.enums.document_status import DocumentStatus
from app.services.document.document_indexing_service import (
    DocumentIndexingService,
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

    storage = Mock()
    storage.read.return_value = b"fake-pdf-content"

    pdf_processor = Mock()
    pdf_processor.extract_document.return_value = SimpleNamespace(
        pages=[SimpleNamespace()]
    )

    chunking_service = Mock()
    vector_provider = Mock()

    dependencies = {
        "document_id": document_id,
        "repository": repository,
        "chunk_repository": chunk_repository,
        "storage": storage,
        "pdf_processor": pdf_processor,
        "chunking_service": chunking_service,
        "vector_provider": vector_provider,
    }

    return dependencies


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

    deps["repository"].update_status.assert_any_call(
        deps["document_id"],
        DocumentStatus.INDEXED,
    )

    deps["vector_provider"].upsert.assert_not_called()
    deps["chunk_repository"].create_many.assert_not_called()


def test_successful_indexing_persists_chunks_and_vectors(
    indexing_dependencies,
):
    from uuid import uuid4

    from app.schemas.embedding import ChunkMetadata

    deps = indexing_dependencies
    document_id = deps["document_id"]
    chunk_id = uuid4()

    metadata = ChunkMetadata(
        source="test.pdf",
        page_number=1,
        chunk_index=0,
    )

    chunk = SimpleNamespace(
        chunk_id=chunk_id,
        document_id=document_id,
        text="Enterprise AI uses a Document Agent.",
        metadata=metadata,
    )

    deps["chunking_service"].chunk_document.return_value = [chunk]
    deps["chunk_repository"].get_by_document_id.return_value = []

    embeddings = Mock()
    embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3]]

    with (
        patch(
            "app.services.document.document_indexing_service.get_embeddings",
            return_value=embeddings,
        ),
        patch(
            "app.services.document.document_indexing_service.VectorMapper.to_vector_points",
            return_value=["vector-point-1"],
        ) as map_vectors,
    ):
        service = build_service(deps)
        service.index_document(document_id)

    embeddings.embed_documents.assert_called_once_with(
        ["Enterprise AI uses a Document Agent."]
    )
    map_vectors.assert_called_once()

    deps["chunk_repository"].create_many.assert_called_once_with(
        [
            {
                "id": chunk_id,
                "document_id": document_id,
                "text": "Enterprise AI uses a Document Agent.",
                "source": "test.pdf",
                "page_number": 1,
                "chunk_index": 0,
            }
        ]
    )

    deps["vector_provider"].delete_by_filter.assert_called_once()
    deps["vector_provider"].upsert.assert_called_once()

    assert (
        deps["vector_provider"].upsert.call_args.kwargs["points"]
        == ["vector-point-1"]
    )

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
            RuntimeError, match="Embedding generation failed"
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

    with (
        patch(
            "app.services.document.document_indexing_service.get_embeddings",
            return_value=embeddings,
        ),
        patch(
            "app.services.document.document_indexing_service.VectorMapper.to_vector_points",
            return_value=["vector-point-1"],
        ),
    ):
        service = build_service(deps)

        with pytest.raises(RuntimeError, match="Qdrant unavailable"):
            service.index_document(deps["document_id"])

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

    old_chunk = {
        "id": uuid4(),
        "document_id": document_id,
        "text": "Old chunk",
    }
    deps["chunk_repository"].get_by_document_id.return_value = [old_chunk]

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

    with (
        patch(
            "app.services.document.document_indexing_service.get_embeddings",
            return_value=embeddings,
        ),
        patch(
            "app.services.document.document_indexing_service.VectorMapper.to_vector_points",
            return_value=["replacement-vector"],
        ),
    ):
        service = build_service(deps)
        service.index_document(document_id)

    deps["vector_provider"].delete_by_filter.assert_called_once()
    deps["chunk_repository"].delete_by_document_id.assert_called_once_with(
        document_id
    )
    deps["chunk_repository"].create_many.assert_called_once()
    deps["vector_provider"].upsert.assert_called_once()
