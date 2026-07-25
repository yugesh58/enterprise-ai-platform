from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection

from app.core.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)


@contextmanager
def get_connection() -> Connection:
    """
    Provide a transactional database connection.
    """

    connection = engine.connect()

    transaction = connection.begin()

    try:
        yield connection
        transaction.commit()

    except Exception:
        transaction.rollback()
        raise

    finally:
        connection.close()