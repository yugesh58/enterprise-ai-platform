from app.storage.file_storage.factory import FileStorageFactory
from app.storage.file_storage.base import FileStorageProvider


def get_storage_provider() -> FileStorageProvider:
    """
    Returns the configured storage provider.
    """

    return FileStorageFactory.get_provider()