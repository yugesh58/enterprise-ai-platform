from abc import ABC, abstractmethod
from typing import Any


class DatabaseProvider(ABC):
    """
    Base interface for all database providers.
    """

    @abstractmethod
    def connect(self) -> None:
        """Initialize the database connection."""

    @abstractmethod
    def execute(self, query: str, params: dict | None = None) -> None:
        """Execute INSERT/UPDATE/DELETE."""

    @abstractmethod
    def fetch_one(self, query: str, params: dict | None = None) -> dict[str, Any] | None:
        """Fetch a single record."""

    @abstractmethod
    def fetch_all(self, query: str, params: dict | None = None) -> list[dict[str, Any]]:
        """Fetch multiple records."""

    @abstractmethod
    def get_schema(self) -> dict:
        """Return database schema."""

    @abstractmethod
    def close(self) -> None:
        """Close all database resources."""