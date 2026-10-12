
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.enums.document_status import DocumentStatus
from app.services.document.document_service import DocumentService


@pytest.fixture
def repository():
    return Mock()


@pytest.fixture
def storage():
    mock = Mock()
    mock.save.return_value = "/tmp/test-document.txt"
    return mock


@pytest.fixture
def service(repository, storage):
    return DocumentService(repository=repository, storage=storage)


def test_new_upload_persists_document_and_requests_indexing(
    service, repository, storage
):
    document_id = uuid4()
    repository.get_by_content_hash.return_value = None
    repository.create.return_value = document_id

    content = b"Integration test document"

    result = service.upload_document(
        filename="test.txt",
        content_type="text/plain",
        content=content,
    )

    assert result == {
        "document_id": document_id,
        "status": DocumentStatus.PROCESSING.value,
        "is_existing": False,
        "should_index": True,
    }

    storage.save.assert_called_once_with(
        filename="test.txt",
        content=content,
    )

    repository.create.assert_called_once()
    create_kwargs = repository.create.call_args.kwargs

    assert create_kwargs["filename"] == "test.txt"
    assert create_kwargs["content_type"] == "text/plain"
    assert create_kwargs["file_size"] == len(content)
    assert create_kwargs["storage_path"] == "/tmp/test-document.txt"
    assert len(create_kwargs["content_hash"]) == 64


def test_existing_indexed_document_is_reused_without_reindexing(
    service, repository, storage
):
    document_id = uuid4()

    repository.get_by_content_hash.return_value = {
        "id": document_id,
        "status": DocumentStatus.INDEXED.value,
    }

    result = service.upload_document(
        filename="duplicate.txt",
        content_type="text/plain",
        content=b"Already indexed content",
    )

    assert result == {
        "document_id": document_id,
        "status": DocumentStatus.INDEXED.value,
        "is_existing": True,
        "should_index": False,
    }

    storage.save.assert_not_called()
    repository.create.assert_not_called()
    repository.update_status.assert_not_called()


def test_existing_failed_document_is_queued_for_reindexing(
    service, repository, storage
):
    document_id = uuid4()

    repository.get_by_content_hash.return_value = {
        "id": document_id,
        "status": DocumentStatus.FAILED.value,
    }

    result = service.upload_document(
        filename="retry.txt",
        content_type="text/plain",
        content=b"Failed document content",
    )

    assert result == {
        "document_id": document_id,
        "status": DocumentStatus.PROCESSING.value,
        "is_existing": True,
        "should_index": True,
    }

    repository.update_status.assert_called_once_with(
        document_id,
        DocumentStatus.PROCESSING,
    )

    storage.save.assert_not_called()
    repository.create.assert_not_called()


@pytest.mark.parametrize(
    ("filename", "content_type", "content", "message"),
    [
        ("", "text/plain", b"content", "Filename cannot be empty."),
        ("test.txt", "text/plain", b"", "Document content cannot be empty."),
        ("test.txt", "", b"content", "Content type cannot be empty."),
    ],
)
def test_upload_rejects_invalid_input(
    service, repository, storage,
    filename, content_type, content, message,
):
    with pytest.raises(ValueError, match=message):
        service.upload_document(
            filename=filename,
            content_type=content_type,
            content=content,
        )

    repository.get_by_content_hash.assert_not_called()
    repository.create.assert_not_called()
    storage.save.assert_not_called()


def test_storage_file_is_deleted_when_repository_create_fails(
    service, repository, storage
):
    repository.get_by_content_hash.return_value = None
    repository.create.side_effect = RuntimeError("Database unavailable")

    # No concurrent request created this document.
    repository.get_by_content_hash.side_effect = [None, None]

    with pytest.raises(RuntimeError, match="Database unavailable"):
        service.upload_document(
            filename="test.txt",
            content_type="text/plain",
            content=b"New document",
        )

    storage.delete.assert_called_once_with("/tmp/test-document.txt")
