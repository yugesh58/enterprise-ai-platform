
from uuid import uuid4
from unittest.mock import MagicMock

import pytest

from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)


def test_get_ids_page_returns_ids_in_order():
    first_id = uuid4()
    second_id = uuid4()

    connection = MagicMock()
    connection.execute.return_value.scalars.return_value.all.return_value = [
        first_id,
        second_id,
    ]

    repository = DocumentChunkRepository(connection)

    result = repository.get_ids_page(limit=2)

    assert result == [first_id, second_id]
    connection.execute.assert_called_once()


def test_get_ids_page_uses_after_id_cursor():
    cursor = uuid4()

    connection = MagicMock()
    connection.execute.return_value.scalars.return_value.all.return_value = []

    repository = DocumentChunkRepository(connection)

    repository.get_ids_page(limit=100, after_id=cursor)

    connection.execute.assert_called_once()


@pytest.mark.parametrize("limit", [0, -1])
def test_get_ids_page_rejects_invalid_limit(limit):
    connection = MagicMock()
    repository = DocumentChunkRepository(connection)

    with pytest.raises(ValueError, match="limit must be greater than zero"):
        repository.get_ids_page(limit=limit)

    connection.execute.assert_not_called()
