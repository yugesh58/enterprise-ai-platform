import importlib
from uuid import uuid4
from unittest.mock import MagicMock
import threading
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

class FakeEvent:
    def __init__(self, wait_results=None):
        self.wait_results = iter(wait_results or [])
        self.is_set_value = False

    def wait(self, timeout=None):
        return next(self.wait_results, True)

    def set(self):
        self.is_set_value = True

    def is_set(self):
        return self.is_set_value


class FakeThread:
    def __init__(self, target, **kwargs):
        self.target = target
        self.started = False
        self.joined = False

    def start(self):
        self.started = True
        self.target()

    def join(self):
        self.joined = True

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
def configure_fake_heartbeat(monkeypatch, wait_results):
    stop_event = FakeEvent(wait_results)
    lock_lost_event = FakeEvent()

    events = iter([stop_event, lock_lost_event])
    monkeypatch.setattr(
        lock_module.threading,
        "Event",
        lambda: next(events),
    )

    threads = []

    def create_thread(target, **kwargs):
        thread = FakeThread(target, **kwargs)
        threads.append(thread)
        return thread

    monkeypatch.setattr(
        lock_module.threading,
        "Thread",
        create_thread,
    )

    return stop_event, lock_lost_event, threads


def test_heartbeat_renews_lock_successfully(mock_lock, monkeypatch):
    document_id, _, lock = mock_lock
    lock.acquire.return_value = True

    _, _, threads = configure_fake_heartbeat(
        monkeypatch,
        [False, True],
    )

    with lock_module.document_index_lock(document_id):
        pass

    lock.extend.assert_called_once_with(
        lock_module.settings.DOCUMENT_INDEX_LOCK_TTL_SECONDS,
        replace_ttl=True,
    )
    assert threads[0].started
    assert threads[0].joined
    lock.release.assert_called_once()


def test_heartbeat_failure_raises_lock_lost(mock_lock, monkeypatch):
    document_id, _, lock = mock_lock
    lock.acquire.return_value = True
    lock.extend.side_effect = redis.RedisError("Redis connection lost")

    _, lock_lost, threads = configure_fake_heartbeat(
        monkeypatch,
        [False, True],
    )

    with pytest.raises(lock_module.DocumentIndexLockLost):
        with lock_module.document_index_lock(document_id):
            pass

    assert lock_lost.is_set()
    assert threads[0].joined
    lock.release.assert_called_once()


def test_lock_released_when_operation_fails(mock_lock, monkeypatch):
    document_id, _, lock = mock_lock
    lock.acquire.return_value = True

    _, _, threads = configure_fake_heartbeat(
        monkeypatch,
        [True],
    )

    with pytest.raises(ValueError, match="Indexing failed"):
        with lock_module.document_index_lock(document_id):
            raise ValueError("Indexing failed")

    assert threads[0].joined
    lock.release.assert_called_once()