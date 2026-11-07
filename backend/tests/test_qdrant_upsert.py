
from unittest.mock import Mock

import pytest
from qdrant_client.models import PointStruct

from app.storage.vectorstore.models.vector_point import VectorPoint
from app.storage.vectorstore.providers.qdrant_provider import QdrantProvider
import httpx
from qdrant_client.http.exceptions import UnexpectedResponse

@pytest.fixture
def provider():
    instance = QdrantProvider()
    instance._client = Mock()
    instance._ensure_collection_exists = Mock()
    instance._validate_collection = Mock()
    return instance


def test_upsert_converts_vector_points_to_qdrant_points(provider):
    points = [
        VectorPoint(
            id="chunk-1",
            vector=[0.1, 0.2, 0.3],
            payload={"text": "First document chunk"},
        ),
        VectorPoint(
            id="chunk-2",
            vector=[0.4, 0.5, 0.6],
            payload={"text": "Second document chunk"},
        ),
    ]

    provider.upsert(
        collection_name="test_collection",
        points=points,
    )

    provider._ensure_collection_exists.assert_called_once_with(
        collection_name="test_collection",
        vector_size=3,
    )

    provider._client.upsert.assert_called_once()

    call_kwargs = provider._client.upsert.call_args.kwargs

    assert call_kwargs["collection_name"] == "test_collection"
    assert len(call_kwargs["points"]) == 2

    first_point, second_point = call_kwargs["points"]

    assert isinstance(first_point, PointStruct)
    assert first_point.id == "chunk-1"
    assert first_point.vector == [0.1, 0.2, 0.3]
    assert first_point.payload == {"text": "First document chunk"}

    assert second_point.id == "chunk-2"
    assert second_point.vector == [0.4, 0.5, 0.6]
    assert second_point.payload == {"text": "Second document chunk"}


def test_upsert_with_no_points_does_nothing(provider):
    provider.upsert(
        collection_name="test_collection",
        points=[],
    )

    provider._client.upsert.assert_not_called()
    provider._ensure_collection_exists.assert_not_called()


def test_upsert_rejects_inconsistent_vector_dimensions(provider):
    points = [
        VectorPoint(
            id="chunk-1",
            vector=[0.1, 0.2, 0.3],
            payload={},
        ),
        VectorPoint(
            id="chunk-2",
            vector=[0.4, 0.5],
            payload={},
        ),
    ]

    with pytest.raises(
        ValueError,
        match="All vectors in a single upsert operation",
    ):
        provider.upsert(
            collection_name="test_collection",
            points=points,
        )

    provider._client.upsert.assert_not_called()


def test_upsert_requires_connection():
    provider = QdrantProvider()

    with pytest.raises(
        RuntimeError,
        match="Qdrant client is not connected",
    ):
        provider.upsert(
            collection_name="test_collection",
            points=[
                VectorPoint(
                    id="chunk-1",
                    vector=[0.1, 0.2, 0.3],
                    payload={},
                )
            ],
        )
def test_scroll_returns_point_ids_and_payloads(provider):
    from types import SimpleNamespace

    provider._client.scroll.return_value = (
        [
            SimpleNamespace(
                id="chunk-1",
                payload={"document_id": "document-1"},
            ),
            SimpleNamespace(
                id="chunk-2",
                payload={"document_id": "document-1"},
            ),
        ],
        "chunk-2",
    )

    points, next_offset = provider.scroll(
        collection_name="test_collection",
        limit=2,
    )

    assert points == [
        {
            "id": "chunk-1",
            "payload": {"document_id": "document-1"},
        },
        {
            "id": "chunk-2",
            "payload": {"document_id": "document-1"},
        },
    ]
    assert next_offset == "chunk-2"

    provider._client.scroll.assert_called_once_with(
        collection_name="test_collection",
        limit=2,
        offset=None,
        with_payload=True,
        with_vectors=False,
    )


def test_scroll_passes_pagination_offset(provider):
    provider._client.scroll.return_value = ([], None)

    points, next_offset = provider.scroll(
        collection_name="test_collection",
        limit=100,
        offset="chunk-50",
    )

    assert points == []
    assert next_offset is None

    assert provider._client.scroll.call_args.kwargs["offset"] == "chunk-50"


def test_scroll_rejects_non_positive_limit(provider):
    with pytest.raises(ValueError, match="Scroll limit"):
        provider.scroll(
            collection_name="test_collection",
            limit=0,
        )


def test_scroll_requires_connection():
    provider = QdrantProvider()

    with pytest.raises(RuntimeError, match="not connected"):
        provider.scroll("test_collection")

def test_upsert_retries_after_transient_failure(provider, monkeypatch):
    import app.storage.vectorstore.providers.qdrant_provider as module

    sleep = Mock()
    monkeypatch.setattr(module.time, "sleep", sleep)

    provider._client.upsert.side_effect = [
        httpx.ConnectError("Connection unavailable"),
        None,
    ]

    points = [
        VectorPoint(
            id="chunk-1",
            vector=[0.1, 0.2, 0.3],
            payload={},
        )
    ]

    provider.upsert("test_collection", points)

    assert provider._client.upsert.call_count == 2
    sleep.assert_called_once()

def test_upsert_retries_after_qdrant_server_error(provider, monkeypatch):
    import app.storage.vectorstore.providers.qdrant_provider as module

    sleep = Mock()
    monkeypatch.setattr(module.time, "sleep", sleep)

    provider._client.upsert.side_effect = [
        UnexpectedResponse(
            status_code=503,
            reason_phrase="Service Unavailable",
            content=b"Unavailable",
            headers={},
        ),
        None,
    ]

    points = [
        VectorPoint(
            id="chunk-1",
            vector=[0.1, 0.2, 0.3],
            payload={},
        )
    ]

    provider.upsert("test_collection", points)

    assert provider._client.upsert.call_count == 2
    sleep.assert_called_once()

def test_upsert_stops_after_max_retries(provider, monkeypatch):
    import app.storage.vectorstore.providers.qdrant_provider as module

    sleep = Mock()
    monkeypatch.setattr(module.time, "sleep", sleep)
    monkeypatch.setattr(
        module.settings,
        "QDRANT_UPSERT_MAX_RETRIES",
        2,
    )

    provider._client.upsert.side_effect = httpx.ConnectError(
        "Connection unavailable"
    )

    points = [
        VectorPoint(
            id="chunk-1",
            vector=[0.1, 0.2, 0.3],
            payload={},
        )
    ]

    with pytest.raises(httpx.ConnectError):
        provider.upsert("test_collection", points)

    assert provider._client.upsert.call_count == 3
    assert sleep.call_count == 2

def test_upsert_does_not_retry_permanent_qdrant_error(
    provider,
    monkeypatch,
):
    import app.storage.vectorstore.providers.qdrant_provider as module

    sleep = Mock()
    monkeypatch.setattr(module.time, "sleep", sleep)

    provider._client.upsert.side_effect = UnexpectedResponse(
        status_code=400,
        reason_phrase="Bad Request",
        content=b"Invalid request",
        headers={},
    )

    points = [
        VectorPoint(
            id="chunk-1",
            vector=[0.1, 0.2, 0.3],
            payload={},
        )
    ]

    with pytest.raises(UnexpectedResponse):
        provider.upsert("test_collection", points)

    provider._client.upsert.assert_called_once()
    sleep.assert_not_called()