
from collections.abc import Generator

from sqlalchemy.orm import Session

from app.storage.database.connection import get_document_connection


def get_db() -> Generator[Session, None, None]:
    """Provide a database session for document repositories."""
    session = get_document_connection()

    try:
        yield session
    finally:
        session.close()
