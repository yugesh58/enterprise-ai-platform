from pathlib import Path

from app.core.config import settings
from app.storage.file_storage.providers.local_storage_provider import (
    LocalStorageProvider,
)


class FileStorageFactory:

    _provider = None

    @classmethod
    def get_provider(cls):

        if cls._provider is None:
            cls._provider = LocalStorageProvider(
                root_directory=Path(settings.UPLOAD_DIRECTORY)
            )

        return cls._provider