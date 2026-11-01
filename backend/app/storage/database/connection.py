from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import settings


def _create_postgres_engine(database_url: str) -> Engine:
    return create_engine(
        database_url,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
        pool_pre_ping=True,
        echo=settings.DATABASE_ECHO,
    )


# SQL Agent — PostgreSQL on port 5432
sql_engine: Engine = _create_postgres_engine(
    settings.DATABASE_URL,
)

# Document Agent — PostgreSQL on port 5433
document_engine: Engine = _create_postgres_engine(
    settings.DOCUMENT_DATABASE_URL,
)


def get_connection() -> Session:
    """Return a session for the SQL Agent database."""
    return Session(sql_engine)


def get_document_connection() -> Session:
    """Return a session for the document metadata database."""
    return Session(document_engine)


def dispose_database_engines() -> None:
    """Dispose shared PostgreSQL engines during application shutdown."""
    sql_engine.dispose()
    document_engine.dispose()