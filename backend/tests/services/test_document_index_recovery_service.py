from contextlib import nullcontext
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.services.document.document_index_lock import (
    DocumentIndexingAlreadyInProgress,
    DocumentIndexLockLost,
    DocumentIndexLockUnavailable,
)
from app.services.document.document_index_recovery_service import (
    DocumentIndexRecoveryService,
)


@pytest.fixture
def repository():
    return Mock()


@pytest.fixture
def service(repository):
    return DocumentIndexRecoveryService(
        repository=repository,
        stale_timeout_seconds=3600,
    )


def test_recovers_stale_documents(service, repository, monkeypatch):
    document_id = uuid4()
    repository.get_stale_processing_ids.return_value = [document_id]
    repository.mark_failed_if_stale.return_value = True

    monkeypatch.setattr(
        "app.services.document.document_index_recovery_service.document_index_lock",
        lambda document_id: nullcontext(),
    )

    result = service.recover_stale_documents()

    assert result["scanned"] == 1
    assert result["recovered"] == 1
    assert result["skipped"] == 0
    assert result["recovered_document_ids"] == [str(document_id)]

    repository.mark_failed_if_stale.assert_called_once_with(
        document_id,
        3600,
    )


def test_skips_document_with_active_lock(service, repository, monkeypatch):
    document_id = uuid4()
    repository.get_stale_processing_ids.return_value = [document_id]

    def active_lock(_document_id):
        raise DocumentIndexingAlreadyInProgress()

    monkeypatch.setattr(
        "app.services.document.document_index_recovery_service.document_index_lock",
        active_lock,
    )

    result = service.recover_stale_documents()

    assert result["scanned"] == 1
    assert result["recovered"] == 0
    assert result["skipped"] == 1
    repository.mark_failed_if_stale.assert_not_called()


def test_skips_document_that_is_no_longer_stale(
    service,
    repository,
    monkeypatch,
):
    document_id = uuid4()
    repository.get_stale_processing_ids.return_value = [document_id]
    repository.mark_failed_if_stale.return_value = False

    monkeypatch.setattr(
        "app.services.document.document_index_recovery_service.document_index_lock",
        lambda document_id: nullcontext(),
    )

    result = service.recover_stale_documents()

    assert result["recovered"] == 0
    assert result["skipped"] == 1


@pytest.mark.parametrize(
    "lock_error",
    [
        DocumentIndexLockUnavailable("Redis unavailable"),
        DocumentIndexLockLost("Lock ownership lost"),
    ],
)
def test_fails_closed_on_lock_errors(
    service,
    repository,
    monkeypatch,
    lock_error,
):
    document_id = uuid4()
    repository.get_stale_processing_ids.return_value = [document_id]

    def failing_lock(_document_id):
        raise lock_error

    monkeypatch.setattr(
        "app.services.document.document_index_recovery_service.document_index_lock",
        failing_lock,
    )

    with pytest.raises(type(lock_error)):
        service.recover_stale_documents()

    repository.mark_failed_if_stale.assert_not_called()


def test_rejects_nonpositive_timeout(repository):
    with pytest.raises(ValueError, match="greater than zero"):
        DocumentIndexRecoveryService(
            repository=repository,
            stale_timeout_seconds=0,
        )


def test_handles_no_stale_documents(service, repository):
    repository.get_stale_processing_ids.return_value = []

    result = service.recover_stale_documents()

    assert result == {
        "scanned": 0,
        "recovered": 0,
        "skipped": 0,
        "recovered_document_ids": [],
        "skipped_document_ids": [],
    }
