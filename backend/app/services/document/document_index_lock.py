import threading
from contextlib import contextmanager
from collections.abc import Iterator
from uuid import UUID

import redis

from app.core.config import settings
from app.storage.redis_client import get_redis_client


class DocumentIndexingAlreadyInProgress(RuntimeError):
    """Raised when another worker is indexing the same document."""


class DocumentIndexLockUnavailable(RuntimeError):
    """Raised when the distributed locking service is unavailable."""


class DocumentIndexLockLost(RuntimeError):
    """Raised when the worker loses ownership of its indexing lock."""


@contextmanager
def document_index_lock(document_id: UUID) -> Iterator[None]:
    try:
        client = get_redis_client()

        lock = client.lock(
            name=f"document-index:{document_id}",
            timeout=settings.DOCUMENT_INDEX_LOCK_TTL_SECONDS,
            blocking=False,
            thread_local=False,
        )

        acquired = lock.acquire(blocking=False)

    except redis.RedisError as exc:
        raise DocumentIndexLockUnavailable(
            "Unable to acquire document indexing lock."
        ) from exc

    if not acquired:
        raise DocumentIndexingAlreadyInProgress(
            f"Document {document_id} is already being indexed."
        )

    stop_event = threading.Event()
    lock_lost = threading.Event()

    def renew_lock() -> None:
        while not stop_event.wait(
            settings.DOCUMENT_INDEX_LOCK_RENEWAL_INTERVAL_SECONDS
        ):
            try:
                lock.extend(
                    settings.DOCUMENT_INDEX_LOCK_TTL_SECONDS,
                    replace_ttl=True,
                )
            except redis.RedisError:
                lock_lost.set()
                return

    heartbeat = threading.Thread(
        target=renew_lock,
        name=f"document-index-lock-{document_id}",
        daemon=True,
    )

    heartbeat.start()

    try:
        yield

    finally:
        stop_event.set()
        heartbeat.join()

        try:
            lock.release()
        except redis.RedisError:
            # Ownership may already have expired or been lost.
            pass

    if lock_lost.is_set():
        raise DocumentIndexLockLost(
            f"Lost Redis lock ownership for document {document_id}."
        )