from fastapi import Depends
from sqlalchemy.engine import Connection

from app.api.dependencies.database import get_db
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.repositories.document_repository import DocumentRepository


def get_document_repository(
    connection: Connection = Depends(get_db),
) -> DocumentRepository:
    """
    Returns the document repository.
    """

    return DocumentRepository(connection)


def get_document_chunk_repository(
    connection: Connection = Depends(get_db),
) -> DocumentChunkRepository:
    """
    Returns the document chunk repository.
    """

    return DocumentChunkRepository(connection)