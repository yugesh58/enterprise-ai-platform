
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.storage.database.base import DatabaseProvider
from app.storage.database.connection import sql_engine


class PostgreSQLProvider(DatabaseProvider):
    """PostgreSQL implementation of DatabaseProvider."""

    def __init__(self) -> None:
        self._engine: Engine | None = None

    def connect(self) -> None:
        """Reuse the shared SQL Agent PostgreSQL engine."""
        if self._engine is None:
            self._engine = sql_engine

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

    def fetch_all(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        self.connect()
        assert self._engine is not None

        with self._engine.begin() as connection:
            connection.execute(
                text(
                    f"SET LOCAL statement_timeout = "
                    f"{settings.SQL_QUERY_TIMEOUT_MS}"
                )
            )
            result = connection.execute(text(query), params or {})

        return [dict(row) for row in result.mappings().all()]

    def get_schema(self) -> dict[str, Any]:
        """Return complete database schema metadata."""
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

    def close(self) -> None:
        """Release this provider's reference, not the shared engine."""
        self._engine = None
