from app.storage.database.base import DatabaseProvider
from app.storage.database.connection import engine
from sqlalchemy import inspect
from typing import Any
from sqlalchemy import text





class SQLiteProvider(DatabaseProvider):
    def connect(self) -> None:
        pass

    def _execute_query(
    self,
    query: str,
    params: dict[str, Any] | None = None,
        ):
        params = params or {}

        with self.connect() as connection:
            return connection.execute(text(query), params)

    def execute(self, query: str, params: tuple | None = None):
        return self._execute_query(query, params)

    def fetch_one(self, query: str, params: tuple | None = None):
        result = self._execute_query(query, params)
        row = result.fetchone()
        return dict(row._mapping) if row else None

    def fetch_all(self, query: str, params: tuple | None = None):
        result = self._execute_query(query, params)
        return [dict(row._mapping) for row in result.fetchall()]
        
    def get_schema(self):
        inspector = inspect(engine)

        schema_info = []

        tables = inspector.get_table_names()

        for table in tables:
            columns = inspector.get_columns(table)
            column_names = [column["name"] for column in columns]
            schema_info.append(f"{table}({', '.join(column_names)})")

        return "\n".join(schema_info)

    def close(self) -> None:
        engine.dispose()