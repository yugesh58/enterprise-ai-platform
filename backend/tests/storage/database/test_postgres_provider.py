from app.storage.database.providers import postgres_provider
from app.storage.database.providers.postgres_provider import PostgreSQLProvider


def test_sql_engine_uses_sql_agent_database_url():
    from app.core.config import settings
    from sqlalchemy.engine import make_url
    from app.storage.database.connection import sql_engine

    expected_url = make_url(settings.SQL_AGENT_DATABASE_URL)
    matches = (
        sql_engine.url.username == expected_url.username
        and sql_engine.url.password == expected_url.password
        and sql_engine.url.host == expected_url.host
        and sql_engine.url.port == expected_url.port
        and sql_engine.url.database == expected_url.database
    )

    assert matches, "SQL Agent engine must use SQL_AGENT_DATABASE_URL."


class FakeInspector:
    def get_table_names(self, schema):
        assert schema == "public"
        return [
            "employees",
            "llm_usage_events",
            "documents",
            "departments",
        ]

    def get_columns(self, table_name, schema):
        assert schema == "public"
        return [{"name": f"{table_name}_id", "type": "INTEGER", "nullable": False}]

    def get_pk_constraint(self, table_name, schema):
        return {"constrained_columns": [f"{table_name}_id"]}

    def get_foreign_keys(self, table_name, schema):
        return []

    def get_indexes(self, table_name, schema):
        return []


def test_schema_exposes_only_approved_public_sample_tables(monkeypatch):
    provider = PostgreSQLProvider()
    provider._engine = object()
    monkeypatch.setattr(
        postgres_provider,
        "inspect",
        lambda _engine: FakeInspector(),
    )

    schema = provider.get_schema()

    assert set(schema) == {"employees", "departments"}
