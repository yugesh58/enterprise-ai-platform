from app.core.config import settings
from app.storage.database.base import DatabaseProvider
from app.storage.database.registry import DatabaseRegistry


class DatabaseFactory:
    """
    Creates the configured database provider.
    """

    @staticmethod
    def create() -> DatabaseProvider:
        provider_class = DatabaseRegistry.get(settings.DATABASE_PROVIDER)
        return provider_class()