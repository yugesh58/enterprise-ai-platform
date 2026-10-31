from pathlib import Path
from tempfile import TemporaryDirectory
import pytest
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
def test_rejects_relative_path_traversal(tmp_path):
    provider = LocalStorageProvider(tmp_path / "uploads")

    with pytest.raises(ValueError, match="outside the allowed directory"):
        provider.exists("../outside.txt")
def test_rejects_absolute_path_outside_storage(tmp_path):
    provider = LocalStorageProvider(tmp_path / "uploads")
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("sensitive data")

    with pytest.raises(ValueError, match="outside the allowed directory"):
        provider.read(outside_file)
def test_rejects_symlink_path_escape(tmp_path):
    provider = LocalStorageProvider(tmp_path / "uploads")

    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("sensitive data")

    symlink = provider._root_directory / "outside-link.txt"

    try:
        symlink.symlink_to(outside_file)
    except OSError:
        pytest.skip("Symlinks are not supported in this environment.")

    with pytest.raises(ValueError, match="outside the allowed directory"):
        provider.read(symlink)