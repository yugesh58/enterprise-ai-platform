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

    def __init__(self):
        self._client = None

    def _ensure_connected(self) -> None:
        if self._client is None:
            raise RuntimeError(
                "Qdrant client is not connected."
            )

    def connect(self) -> None:
        """
        Establish connection with Qdrant.
        """

        if self._client is not None:
            return

        self._client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )

        self._client.get_collections()

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

        distance_map = {
            "COSINE": Distance.COSINE,
            "DOT": Distance.DOT,
            "EUCLID": Distance.EUCLID,
        }

        distance_enum = distance_map.get(distance.upper())

        if distance_enum is None:
            raise ValueError(
                f"Unsupported distance metric: {distance}"
            )

        existing = {
            collection.name
            for collection in self._client.get_collections().collections
        }

        if collection_name in existing:
            return

        self._client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=distance_enum,
            ),
        )

    def upsert(
        self,
        collection_name: str,
        points: list[VectorPoint],
    ) -> None:

        self._ensure_connected()

        if not points:
            return

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

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
        filters: Optional[dict] = None,
    ) -> list[dict]:

        self._ensure_connected()

        query_filter = None
        print("Filters:", filters)
        if filters:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                    for key, value in filters.items()
                ]
            )
            print("=" * 60)
            print("Searching collection:", collection_name)

            collections = self._client.get_collections()

            print("Available collections:")
            for c in collections.collections:
                print("-", c.name)

            info = self._client.get_collection(collection_name)
            print("Points in collection:", info.points_count)
            print("=" * 60)

        

        results = self._client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
        )
        print(results)

        return [
            {
                "id": str(point.id),
                "score": point.score,
                "payload": point.payload,
            }
            for point in results.points
        ]

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

    def delete_collection(
        self,
        collection_name: str,
    ) -> None:

        self._ensure_connected()

        existing = {
            collection.name
            for collection in self._client.get_collections().collections
        }

        if collection_name not in existing:
            return

        self._client.delete_collection(
            collection_name=collection_name,
        )

    def close(self) -> None:
        self._client = None