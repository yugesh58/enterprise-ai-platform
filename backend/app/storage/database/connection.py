
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import settings


# SQL Agent — PostgreSQL 16 on localhost:5432
sql_engine: Engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

# Document Agent — PostgreSQL 17 on localhost:5433
document_engine: Engine = create_engine(
    settings.DOCUMENT_DATABASE_URL,
    pool_pre_ping=True,
)


def get_connection() -> Session:
    """Return a session for the SQL Agent database."""
    return Session(sql_engine)


def get_document_connection() -> Session:
    """Return a session for the document metadata database."""
    return Session(document_engine)
