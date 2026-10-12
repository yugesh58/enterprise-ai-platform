
from unittest.mock import Mock

import pytest
from qdrant_client.models import PointStruct

from app.storage.vectorstore.models.vector_point import VectorPoint
from app.storage.vectorstore.providers.qdrant_provider import QdrantProvider


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
