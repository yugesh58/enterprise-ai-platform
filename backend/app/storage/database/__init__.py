from app.storage.database.providers.sqlite_provider import SQLiteProvider
from app.storage.database.providers.postgres_provider import PostgreSQLProvider

from app.storage.database.registry import DatabaseRegistry


DatabaseRegistry.register("sqlite", SQLiteProvider)
DatabaseRegistry.register("postgres", PostgreSQLProvider)