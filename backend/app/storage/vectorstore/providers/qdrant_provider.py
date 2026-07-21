from qdrant_client import QdrantClient

from app.core.config import settings
from app.storage.vectorstore.base import VectorProvider
from qdrant_client.http.models import Distance, VectorParams

from qdrant_client.models import PointStruct
from app.storage.vectorstore.models.vector_point import VectorPoint

from qdrant_client.models import PointIdsList

class QdrantProvider(VectorProvider):

    def __init__(self):
        self._client = None

    def connect(self):
        """
        Establish a connection to the Qdrant server.
        """
        self._client = QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        )

        # Verify the connection
        self._client.get_collections()

    def create_collection(
    self,
    collection_name: str,
    vector_size: int,
    distance: str = "COSINE",
    ) -> None:
        """
        Create a Qdrant collection if it does not already exist.
        """
        if vector_size <= 0:
          raise ValueError("vector_size must be greater than zero.")
        collections = self._client.get_collections()

        existing = {
            collection.name
            for collection in collections.collections
        }

        if collection_name in existing:
            return

        distance_map = {
            "COSINE": Distance.COSINE,
            "DOT": Distance.DOT,
            "EUCLID": Distance.EUCLID,
            }

        self._client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
            distance=distance_map[distance],
            ),
        )

    def delete_collection(self, collection_name):
        pass

    def upsert(
    self,
    collection_name: str,
    points: list[VectorPoint],
    ) -> None:
        """
        Insert or update vector points in a Qdrant collection.
        """

        if not points:
            return

        qdrant_points = [
            PointStruct(
            id=point.id,
            vector=point.vector,
            payload=point.payload,
            )
            for point in points
        ]

        self._client.upsert(
            collection_name=collection_name,
            points=qdrant_points,
        )

    def search(
    self,
    collection_name: str,
    query_vector: list[float],
    limit: int = 5,
    ) -> list[dict]:
        """
        Search for similar vectors in a collection.
        """

        results = self._client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
        )

        matches = []

        for point in results.points:
            matches.append(
            {
                "id": str(point.id),
                "score": point.score,
                "payload": point.payload,
            }
        )

        return matches

    def delete(
    self,
    collection_name: str,
    point_ids: list[str],
    ) -> None:
        """
        Delete vector points from a Qdrant collection.
        """

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
        """
        Delete a Qdrant collection.
        """

        collections = self._client.get_collections()

        existing = {
            collection.name
            for collection in collections.collections
        }

        if collection_name not in existing:
            return

        self._client.delete_collection(
            collection_name=collection_name,
        )

    def close(self) -> close:
        self._client = None