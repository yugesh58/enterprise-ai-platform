from pathlib import Path
from tempfile import TemporaryDirectory

from app.storage.file_storage.providers.local_storage_provider import (
    LocalStorageProvider,
)


def test_file_lifecycle():
    with TemporaryDirectory() as temp_dir:

        provider = LocalStorageProvider(
            Path(temp_dir)
        )

        file_path = provider.save(
            filename="resume.pdf",
            content=b"Hello World",
        )

        assert provider.exists(file_path)

        provider.delete(file_path)

        assert not provider.exists(file_path)