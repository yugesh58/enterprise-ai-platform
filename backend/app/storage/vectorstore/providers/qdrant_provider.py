from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
    PointIdsList,
    PointStruct,
)

from app.core.config import settings
from app.storage.vectorstore.base import VectorProvider
from app.storage.vectorstore.models.vector_point import VectorPoint


class QdrantProvider(VectorProvider):
    """
    Production-oriented Qdrant vector provider.

    Responsibilities:
    - Manage the Qdrant connection.
    - Initialize and validate the configured collection.
    - Insert/update vector points.
    - Perform similarity search.
    - Apply metadata filters.
    - Delete vectors and collections.
    """

    def __init__(self) -> None:
        self._client: QdrantClient | None = None

    # ==========================================================
    # Connection
    # ==========================================================

    def _ensure_connected(self) -> None:
        if self._client is None:
            raise RuntimeError(
                "Qdrant client is not connected."
            )

    def connect(self) -> None:
        """
        Establish the Qdrant connection and validate the
        configured collection.
        """

        if self._client is not None:
            return

        self._client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )

        # Fail fast if Qdrant is unavailable.
        self._client.get_collections()

        self._ensure_collection_exists(
            collection_name=settings.QDRANT_COLLECTION,
            vector_size=settings.QDRANT_VECTOR_SIZE,
        )

    # ==========================================================
    # Collection Management
    # ==========================================================

    @staticmethod
    def _get_distance(distance: str) -> Distance:
        distance_map = {
            "COSINE": Distance.COSINE,
            "DOT": Distance.DOT,
            "EUCLID": Distance.EUCLID,
        }

        distance_enum = distance_map.get(
            distance.upper()
        )

        if distance_enum is None:
            raise ValueError(
                f"Unsupported Qdrant distance metric: {distance}"
            )

        return distance_enum

    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: str = "COSINE",
    ) -> None:

        self._ensure_connected()

        if vector_size <= 0:
            raise ValueError(
                "vector_size must be greater than zero."
            )

        distance_enum = self._get_distance(distance)

        existing_collections = {
            collection.name
            for collection in (
                self._client.get_collections().collections
            )
        }

        if collection_name in existing_collections:
            return

        self._client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=distance_enum,
            ),
        )

    def _ensure_collection_exists(
        self,
        collection_name: str,
        vector_size: int,
    ) -> None:

        self._ensure_connected()

        existing_collections = {
            collection.name
            for collection in (
                self._client.get_collections().collections
            )
        }

        if collection_name not in existing_collections:

            self.create_collection(
                collection_name=collection_name,
                vector_size=vector_size,
                distance=settings.QDRANT_DISTANCE,
            )

            return

        self._validate_collection(
            collection_name=collection_name,
            expected_vector_size=vector_size,
        )

    def _validate_collection(
        self,
        collection_name: str,
        expected_vector_size: int,
    ) -> None:

        self._ensure_connected()

        info = self._client.get_collection(
            collection_name
        )

        actual_size = info.config.params.vectors.size

        if actual_size != expected_vector_size:

            raise RuntimeError(
                "Qdrant vector dimension mismatch. "
                f"Collection '{collection_name}' uses "
                f"{actual_size} dimensions, but the application "
                f"is configured for {expected_vector_size}."
            )

    # ==========================================================
    # Upsert
    # ==========================================================

    def upsert(
        self,
        collection_name: str,
        points: list[VectorPoint],
    ) -> None:

        self._ensure_connected()

        if not points:
            return

        vector_size = len(points[0].vector)

        self._ensure_collection_exists(
            collection_name=collection_name,
            vector_size=vector_size,
        )

        for point in points:

            if len(point.vector) != vector_size:
                raise ValueError(
                    "All vectors in a single upsert operation "
                    "must have the same dimension."
                )

        self._client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=point.id,
                    vector=point.vector,
                    payload=point.payload,
                )
                for point in points
            ],
        )

    # ==========================================================
    # Search
    # ==========================================================

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
        filters: Optional[dict] = None,
    ) -> list[dict]:

        self._ensure_connected()

        if not query_vector:
            raise ValueError(
                "query_vector cannot be empty."
            )

        if limit <= 0:
            raise ValueError(
                "Search limit must be greater than zero."
            )

        self._validate_collection(
            collection_name=collection_name,
            expected_vector_size=len(query_vector),
        )

        query_filter = None

        if filters:

            query_filter = Filter(
                must=[
                    FieldCondition(
                        key=key,
                        match=MatchValue(
                            value=value
                        ),
                    )
                    for key, value in filters.items()
                ]
            )

        results = self._client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
        )

        return [
            {
                "id": str(point.id),
                "score": point.score,
                "payload": point.payload,
            }
            for point in results.points
        ]

    # ==========================================================
    # Delete Vectors
    # ==========================================================

    def delete(
        self,
        collection_name: str,
        point_ids: list[str],
    ) -> None:

        self._ensure_connected()

        if not point_ids:
            return

        self._client.delete(
            collection_name=collection_name,
            points_selector=PointIdsList(
                points=point_ids,
            ),
        )

    # ==========================================================
    # Delete Collection
    # ==========================================================

    def delete_collection(
        self,
        collection_name: str,
    ) -> None:

        self._ensure_connected()

        existing_collections = {
            collection.name
            for collection in (
                self._client.get_collections().collections
            )
        }

        if collection_name not in existing_collections:
            return

        self._client.delete_collection(
            collection_name=collection_name,
        )

    # ==========================================================
    # Close
    # ==========================================================

    def close(self) -> None:

        if self._client is not None:

            self._client.close()

            self._client = None