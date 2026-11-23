
import json
from unittest.mock import MagicMock

import pytest

from app.storage.memory.providers import redis_memory


@pytest.fixture
def mock_redis(monkeypatch):
    client = MagicMock()
    pipeline = MagicMock()

    client.pipeline.return_value.__enter__.return_value = pipeline

    monkeypatch.setattr(
        redis_memory,
        "get_redis_client",
        lambda: client,
    )

    return client, pipeline


def test_add_message_stores_message_atomically(mock_redis):
    client, pipeline = mock_redis
    memory = redis_memory.RedisMemory()

    memory.add_message("conversation-123", "user", "Hello")

    key = memory._get_key("conversation-123")

    stored_message = json.loads(
        pipeline.rpush.call_args.args[1]
    )

    assert stored_message == {
        "role": "user",
        "content": "Hello",
    }

    pipeline.rpush.assert_called_once()
    pipeline.ltrim.assert_called_once_with(key, -10, -1)
    pipeline.expire.assert_called_once_with(key, 86400)
    pipeline.execute.assert_called_once()


def test_get_history_returns_chronological_messages(mock_redis):
    client, _ = mock_redis
    memory = redis_memory.RedisMemory()

    client.lrange.return_value = [
        json.dumps({"role": "user", "content": "Hello"}),
        json.dumps({"role": "assistant", "content": "Hi"}),
    ]

    history = memory.get_history("conversation-123")

    assert history == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ]


def test_get_history_respects_requested_limit(mock_redis):
    client, _ = mock_redis
    memory = redis_memory.RedisMemory(max_messages=10)

    memory.get_history("conversation-123", limit=3)

    key = memory._get_key("conversation-123")
    client.lrange.assert_called_once_with(key, -3, -1)


def test_get_history_returns_empty_for_nonpositive_limit(mock_redis):
    client, _ = mock_redis
    memory = redis_memory.RedisMemory()

    assert memory.get_history("conversation-123", limit=0) == []
    client.lrange.assert_not_called()


def test_clear_deletes_conversation(mock_redis):
    client, _ = mock_redis
    memory = redis_memory.RedisMemory()

    memory.clear("conversation-123")

    client.delete.assert_called_once_with(
        memory._get_key("conversation-123")
    )


@pytest.mark.parametrize(
    "conversation_id",
    ["", "x" * 129, None],
)
def test_invalid_conversation_id_is_rejected(
    mock_redis,
    conversation_id,
):
    _, _ = mock_redis
    memory = redis_memory.RedisMemory()

    with pytest.raises(ValueError):
        memory.get_history(conversation_id)


def test_invalid_role_is_rejected(mock_redis):
    _, _ = mock_redis
    memory = redis_memory.RedisMemory()

    with pytest.raises(ValueError):
        memory.add_message("conversation-123", "admin", "Hello")


def test_non_string_content_is_rejected(mock_redis):
    _, _ = mock_redis
    memory = redis_memory.RedisMemory()

    with pytest.raises(ValueError):
        memory.add_message("conversation-123", "user", None)

def test_get_history_refreshes_ttl(redis_memory):
    redis_memory_instance = redis_memory
    client = redis_memory_instance["client"]

def test_get_history_refreshes_ttl(mock_redis):
    client, _ = mock_redis
    memory = redis_memory.RedisMemory(ttl_seconds=3600)

    client.lrange.return_value = [
        json.dumps({"role": "user", "content": "Hello"}),
    ]

    memory.get_history("conversation-123")

    key = memory._get_key("conversation-123")

    client.expire.assert_called_once_with(key, 3600)


def test_get_history_does_not_refresh_ttl_for_missing_conversation(
    mock_redis,
):
    client, _ = mock_redis
    memory = redis_memory.RedisMemory()

    client.lrange.return_value = []

    assert memory.get_history("conversation-123") == []

    client.expire.assert_not_called()