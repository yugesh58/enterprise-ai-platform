from typing import Type

from app.storage.database.base import DatabaseProvider


class DatabaseRegistry:
    """
    Registry for database providers.
    """

    _providers: dict[str, Type[DatabaseProvider]] = {}

    @classmethod
    def register(cls, name: str, provider: Type[DatabaseProvider]) -> None:
        cls._providers[name.lower()] = provider

    @classmethod
    def get(cls, name: str):
        provider = cls._providers.get(name.lower())

        if provider is None:
            raise ValueError(f"Database provider '{name}' is not registered.")

        return provider