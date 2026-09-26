from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, inspect, text

from app.storage.database.base import DatabaseProvider


DB_PATH = Path(__file__).resolve().parents[1] / "company.db"

sqlite_engine = create_engine(
    f"sqlite:///{DB_PATH}",
)


class SQLiteProvider(DatabaseProvider):
    """
    SQLite database provider used by the SQL Agent.
    """

    def connect(self):
        """
        Return a SQLAlchemy database connection.
        """
        return sqlite_engine.connect()

    def execute(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ):
        params = params or {}

        with self.connect() as connection:
            result = connection.execute(
                text(query),
                params,
            )
            connection.commit()

            return result

    def fetch_one(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:

        params = params or {}

        with self.connect() as connection:
            result = connection.execute(
                text(query),
                params,
            )

            row = result.fetchone()

            if row is None:
                return None

            return dict(row._mapping)

    def fetch_all(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        params = params or {}

        with self.connect() as connection:
            result = connection.execute(
                text(query),
                params,
            )

            return [
                dict(row._mapping)
                for row in result.fetchall()
            ]

    def get_schema(self) -> str:
        """
        Return a human-readable representation
        of the SQLite database schema.
        """

        inspector = inspect(sqlite_engine)

        schema_info = []

        for table in inspector.get_table_names():

            columns = inspector.get_columns(table)

            column_names = [
                column["name"]
                for column in columns
            ]

            schema_info.append(
                f"{table}({', '.join(column_names)})"
            )

        return "\n".join(schema_info)

    def close(self) -> None:
        """
        Dispose SQLite engine resources.
        """
        sqlite_engine.dispose()