from app.schemas.chunk import DocumentChunk
from app.schemas.embedding import EmbeddedChunk
from app.storage.vectorstore.models.vector_point import VectorPoint


class VectorMapper:
    """
    Converts embedded document chunks into vector points
    understood by the vector database.
    """

    @staticmethod
    def to_vector_points(
        embedded_chunks: list[EmbeddedChunk],
    ) -> list[VectorPoint]:
        """
        Convert embedded chunks into VectorPoint objects.

        Args:
            embedded_chunks:
                Chunks together with their embedding vectors.

        Returns:
            List of VectorPoint objects.
        """

        vector_points: list[VectorPoint] = []

        for chunk in embedded_chunks:

            vector_points.append(
                VectorPoint(
                    id=str(chunk.chunk_id),
                    vector=chunk.embedding,
                    payload={
                        "document_id": str(chunk.document_id),
                        "text": chunk.text,
                        "source": chunk.metadata.source,
                        "page_number": chunk.metadata.page_number,
                        "chunk_index": chunk.metadata.chunk_index,
                    },
                )
            )

        return vector_points