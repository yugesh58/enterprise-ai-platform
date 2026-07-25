from collections.abc import Generator

from sqlalchemy.engine import Connection

from app.storage.database.connection import get_connection


def get_db() -> Generator[Connection, None, None]:
    """
    Provides a database connection.
    """

    connection = get_connection()

    try:
        yield connection
    finally:
        connection.close()