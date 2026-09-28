from app.core.config import settings
from app.storage.database.base import DatabaseProvider
from app.storage.database.registry import DatabaseRegistry

# Import provider registrations.
import app.storage.database.providers  # noqa: F401


class DatabaseFactory:
    @staticmethod
    def create(
        provider_name: str | None = None,
    ) -> DatabaseProvider:

        provider_name = (
            provider_name
            or settings.DATABASE_PROVIDER
        )

        provider_class = DatabaseRegistry.get(
            provider_name
        )

        return provider_class()