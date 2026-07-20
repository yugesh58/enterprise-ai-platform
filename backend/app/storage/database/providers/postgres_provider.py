from typing import Any

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.storage.database.base import DatabaseProvider
from app.storage.database.registry import DatabaseRegistry



class PostgreSQLProvider(DatabaseProvider):
    """
    PostgreSQL implementation of DatabaseProvider.
    """

    def __init__(self) -> None:
        self._engine: Engine | None = None

    def connect(self) -> None:
        """
        Create SQLAlchemy engine.
        """

        if self._engine is not None:
            return

        self._engine = create_engine(
            settings.DATABASE_URL,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            pool_recycle=settings.DATABASE_POOL_RECYCLE,
            echo=settings.DATABASE_ECHO,
            future=True,
        )
    def execute(
        self,
        query: str,
        params: dict[str, Any] | None = None,
        ) -> None:

         self.connect()

         assert self._engine is not None

         with self._engine.begin() as connection:
            connection.execute(text(query), params or {})
    def fetch_one(
        self,
        query: str,
        params: dict[str, Any] | None = None,
        ) -> dict[str, Any] | None:

            self.connect()

            assert self._engine is not None

            with self._engine.connect() as connection:
             result = connection.execute(text(query), params or {})

             row = result.mappings().first()

             return dict(row) if row else None
            
    def close(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def fetch_all(
    self,
    query: str,
    params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        self.connect()

        assert self._engine is not None

        with self._engine.connect() as connection:
            result = connection.execute(text(query), params or {})

            return [dict(row) for row in result.mappings().all()]
    def get_schema(self) -> dict[str, Any]:
        """
         Returns complete database schema metadata.
         """

        self.connect()

        assert self._engine is not None

        inspector = inspect(self._engine)

        schema: dict[str, Any] = {}

        for table in inspector.get_table_names():

            columns = []

            for column in inspector.get_columns(table):
                columns.append(
                {
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column["nullable"],
                    "default": column.get("default"),
                }
            )

            schema[table] = {
            "columns": columns,
            "primary_key": inspector.get_pk_constraint(table),
            "foreign_keys": inspector.get_foreign_keys(table),
            "indexes": inspector.get_indexes(table),
            }

        return schema

DatabaseRegistry.register("postgres", PostgreSQLProvider)