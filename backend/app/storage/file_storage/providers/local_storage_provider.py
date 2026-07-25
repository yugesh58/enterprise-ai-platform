from pathlib import Path

from app.storage.file_storage.base import FileStorageProvider

from datetime import datetime
from uuid import uuid4


class LocalStorageProvider(FileStorageProvider):
    """
    Local disk implementation of the file storage provider.
    """

    def __init__(self, root_directory: Path) -> None:
        self._root_directory = root_directory

        self._root_directory.mkdir(
            parents=True,
            exist_ok=True,
        )
    def save(
    self,
    filename: str,
    content: bytes,
    ) -> Path:
        """
        Save a file and return its storage path.
        """

        # Extract file extension (.pdf, .docx, etc.)
        extension = Path(filename).suffix

        # Create date-based directory
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

        # Generate unique filename
        stored_filename = f"{uuid4()}{extension}"

        # Full file path
        file_path = directory / stored_filename

        # Save file
        file_path.write_bytes(content)

        return file_path
    def exists(
    self,
    path: Path,
    ) -> bool:
        """
        Check if a file exists.
        """

        return path.exists()
    def delete(
    self,
    path: Path,
    ) -> None:
        """
        Delete a file.
        """

        if path.exists():
            path.unlink()
    def read(
    self,
    path: Path, 
    ) -> bytes:
        """
        Read a file from local storage.
        """

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return path.read_bytes()