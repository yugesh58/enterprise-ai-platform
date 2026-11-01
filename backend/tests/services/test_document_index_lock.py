import importlib
from uuid import uuid4
from unittest.mock import MagicMock

import pytest
import redis

lock_module = importlib.import_module(
    "app.services.document.document_index_lock"
)


@pytest.fixture
def mock_lock(monkeypatch):
    document_id = uuid4()

    lock = MagicMock()
    client = MagicMock()
    client.lock.return_value = lock

    monkeypatch.setattr(
        lock_module,
        "get_redis_client",
        lambda: client,
    )

    return document_id, client, lock


def test_lock_acquired_and_released(mock_lock):
    document_id, client, lock = mock_lock
    lock.acquire.return_value = True

    with lock_module.document_index_lock(document_id):
        pass

    client.lock.assert_called_once_with(
        name=f"document-index:{document_id}",
        timeout=lock_module.settings.DOCUMENT_INDEX_LOCK_TTL_SECONDS,
        blocking=False,
        thread_local=False,
    )
    lock.acquire.assert_called_once_with(blocking=False)
    lock.release.assert_called_once()


def test_lock_contention_raises_exception(mock_lock):
    document_id, _, lock = mock_lock
    lock.acquire.return_value = False

    with pytest.raises(
        lock_module.DocumentIndexingAlreadyInProgress
    ):
        with lock_module.document_index_lock(document_id):
            pytest.fail("Execution should not enter the lock")

    lock.release.assert_not_called()


def test_redis_acquisition_error_is_wrapped(mock_lock):
    document_id, _, lock = mock_lock
    lock.acquire.side_effect = redis.RedisError("Redis unavailable")

    with pytest.raises(lock_module.DocumentIndexLockUnavailable):
        with lock_module.document_index_lock(document_id):
            pass

    lock.release.assert_not_called()


def test_redis_client_error_is_wrapped(monkeypatch):
    monkeypatch.setattr(
        lock_module,
        "get_redis_client",
        MagicMock(side_effect=redis.RedisError("Connection failed")),
    )

    with pytest.raises(lock_module.DocumentIndexLockUnavailable):
        with lock_module.document_index_lock(uuid4()):
            pass


def test_release_error_is_suppressed(mock_lock):
    document_id, _, lock = mock_lock
    lock.acquire.return_value = True
    lock.release.side_effect = redis.RedisError("Release failed")

    with lock_module.document_index_lock(document_id):
        pass

    lock.release.assert_called_once()