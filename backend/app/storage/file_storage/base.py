from abc import ABC, abstractmethod
from pathlib import Path


class FileStorageProvider(ABC):
    """
    Base interface for file storage providers.
    """

    @abstractmethod
    def save(
        self,
        filename: str,
        content: bytes,
    ) -> Path:
        """
        Save a file and return its storage path.
        """
        pass

    @abstractmethod
    def read(
        self,
        path: Path,
    ) -> bytes:
        """
        Read a file from storage.
        """
        pass

    @abstractmethod
    def delete(
        self,
        path: Path,
    ) -> None:
        """
        Delete a file.
        """
        pass

    @abstractmethod
    def exists(
        self,
        path: Path,
    ) -> bool:
        """
        Check if a file exists.
        """
        pass