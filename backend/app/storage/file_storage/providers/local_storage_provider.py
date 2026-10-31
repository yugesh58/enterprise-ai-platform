from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.storage.file_storage.base import FileStorageProvider


class LocalStorageProvider(FileStorageProvider):
    """
    Local disk implementation of the file storage provider.
    """

    def __init__(self, root_directory: Path) -> None:
        self._root_directory = root_directory.resolve()
        self._root_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _resolve_path(self, path: str | Path) -> Path:
        """
        Resolve a storage path and ensure it remains inside the storage root.
        """
        candidate = Path(path)

        if not candidate.is_absolute():
            candidate = self._root_directory / candidate

        root = self._root_directory.resolve()
        resolved = candidate.resolve()

        if not resolved.is_relative_to(root):
            raise ValueError("Storage path is outside the allowed directory.")

        return resolved

    def save(
        self,
        filename: str,
        content: bytes,
    ) -> Path:
        """
        Save a file and return its storage path.
        """

        extension = Path(filename).suffix

        today = datetime.now()

        directory = (
            self._root_directory
            / str(today.year)
            / f"{today.month:02d}"
            / f"{today.day:02d}"
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        stored_filename = f"{uuid4()}{extension}"

        file_path = directory / stored_filename

        file_path.write_bytes(content)

        return file_path

    def exists(
        self,
        path: str | Path,
    ) -> bool:
        """
        Check if a file exists.
        """

        path = self._resolve_path(path)

        return path.exists()

    def delete(
        self,
        path: str | Path,
    ) -> None:
        """
        Delete a file.
        """

        path = self._resolve_path(path)

        if path.exists():
            path.unlink()

    def read(
        self,
        path: str | Path,
    ) -> bytes:
        """
        Read a file from local storage.
        """

        path = self._resolve_path(path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return path.read_bytes()