from uuid import UUID

from sqlalchemy import delete, func, insert, select
from sqlalchemy.orm import Session

from app.models.document_chunk import document_chunks


class DocumentChunkRepository:
    """
    Repository responsible for CRUD and search operations on document chunks.
    """

    def __init__(self, connection: Session) -> None:
        self._connection = connection

    def create_many(
        self,
        chunks: list[dict],
    ) -> None:
        """
        Create multiple document chunk records.
        """

        if not chunks:
            return

        statement = insert(document_chunks).values(chunks)

        self._connection.execute(statement)
        self._connection.commit()

    def get_by_document_id(
        self,
        document_id: UUID,
    ) -> list[dict]:
        """
        Return all chunks belonging to a document.
        """

        statement = (
            select(document_chunks)
            .where(document_chunks.c.document_id == document_id)
            .order_by(document_chunks.c.chunk_index)
        )

        result = self._connection.execute(statement)

        return [dict(row) for row in result.mappings().all()]

    def get_ids_by_document_id(
        self,
        document_id: UUID,
    ) -> list[UUID]:
        """
        Return the IDs of all chunks belonging to a document.
        """

        statement = (
            select(document_chunks.c.id)
            .where(document_chunks.c.document_id == document_id)
            .order_by(document_chunks.c.chunk_index)
        )

        result = self._connection.execute(statement)

        return list(result.scalars().all())

    def delete_by_document_id(
        self,
        document_id: UUID,
    ) -> None:
        """
        Delete all chunks belonging to a document.
        """

        statement = (
            delete(document_chunks)
            .where(document_chunks.c.document_id == document_id)
        )

        self._connection.execute(statement)
        self._connection.commit()

    def keyword_search(
        self,
        query: str,
        top_k: int = 5,
        document_id: UUID | None = None,
    ) -> list[dict]:
        """
        Search document chunks using PostgreSQL full-text search.

        PostgreSQL converts the chunk text and user query into searchable
        linguistic representations and ranks matching chunks by relevance.

        Args:
            query: Natural-language search query.
            top_k: Maximum number of results to return.
            document_id: Optional document filter.

        Returns:
            A list of matching chunks with a keyword_score.
        """

        query = query.strip()

        if not query:
            return []

        if top_k <= 0:
            return []

        # Convert chunk text into a PostgreSQL tsvector.
        text_vector = func.to_tsvector(
            "english",
            document_chunks.c.text,
        )

        # Convert the user's natural-language query into a tsquery.
        text_query = func.websearch_to_tsquery(
            "english",
            query,
        )

        # Calculate PostgreSQL relevance score.
        keyword_score = func.ts_rank_cd(
            text_vector,
            text_query,
        ).label("keyword_score")

        statement = (
            select(
                document_chunks,
                keyword_score,
            )
            .where(
                text_vector.op("@@")(text_query),
            )
            .order_by(
                keyword_score.desc(),
                document_chunks.c.chunk_index,
            )
            .limit(top_k)
        )

        if document_id is not None:
            statement = statement.where(
                document_chunks.c.document_id == document_id
            )

        result = self._connection.execute(statement)

        return [
            dict(row)
            for row in result.mappings().all()
        ]