import pytest

from app.storage.memory.providers.local_memory import LocalMemory


@pytest.fixture
def memory():
    return LocalMemory(max_messages=3)


def test_add_and_retrieve_messages(memory):
    memory.add_message("conversation-1", "user", "Hello")
    memory.add_message("conversation-1", "assistant", "Hi")

    assert memory.get_history("conversation-1") == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ]


def test_history_is_limited_to_max_messages(memory):
    for index in range(5):
        memory.add_message(
            "conversation-1",
            "user",
            f"Message {index}",
        )

    history = memory.get_history("conversation-1")

    assert len(history) == 3
    assert history[0]["content"] == "Message 2"


def test_get_history_respects_limit(memory):
    for index in range(3):
        memory.add_message(
            "conversation-1",
            "user",
            f"Message {index}",
        )

    assert len(memory.get_history("conversation-1", limit=2)) == 2
    assert memory.get_history("conversation-1", limit=0) == []


def test_clear_removes_conversation(memory):
    memory.add_message("conversation-1", "user", "Hello")

    memory.clear("conversation-1")

    assert memory.get_history("conversation-1") == []


@pytest.mark.parametrize(
    "conversation_id",
    ["", "x" * 129, None],
)
def test_invalid_conversation_id_is_rejected(memory, conversation_id):
    with pytest.raises(ValueError):
        memory.add_message(conversation_id, "user", "Hello")


@pytest.mark.parametrize(
    "role",
    ["invalid", "", None],
)
def test_invalid_role_is_rejected(memory, role):
    with pytest.raises(ValueError):
        memory.add_message("conversation-1", role, "Hello")


def test_non_string_content_is_rejected(memory):
    with pytest.raises(ValueError):
        memory.add_message("conversation-1", "user", None)

import pytest

from app.storage.memory.providers.local_memory import LocalMemory


def test_expired_conversation_is_removed(monkeypatch):
    current_time = [100.0]

    monkeypatch.setattr(
        "app.storage.memory.providers.local_memory.time.monotonic",
        lambda: current_time[0],
    )

    memory = LocalMemory(
        max_messages=10,
        ttl_seconds=60,
    )

    memory.add_message("conversation-1", "user", "Hello")

    current_time[0] = 161.0

    assert memory.get_history("conversation-1") == []


def test_conversation_access_refreshes_ttl(monkeypatch):
    current_time = [100.0]

    monkeypatch.setattr(
        "app.storage.memory.providers.local_memory.time.monotonic",
        lambda: current_time[0],
    )

    memory = LocalMemory(
        max_messages=10,
        ttl_seconds=60,
    )

    memory.add_message("conversation-1", "user", "Hello")

    current_time[0] = 150.0

    assert memory.get_history("conversation-1")

    current_time[0] = 190.0

    assert memory.get_history("conversation-1")


def test_oldest_conversation_is_evicted_when_limit_reached():
    memory = LocalMemory(
        max_messages=10,
        max_conversations=2,
    )

    memory.add_message("conversation-1", "user", "First")
    memory.add_message("conversation-2", "user", "Second")
    memory.add_message("conversation-3", "user", "Third")

    assert memory.get_history("conversation-1") == []
    assert memory.get_history("conversation-2")
    assert memory.get_history("conversation-3")


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"max_conversations": 0}, "max_conversations"),
        ({"ttl_seconds": 0}, "ttl_seconds"),
    ],
)
def test_invalid_memory_limits_are_rejected(kwargs, error):
    with pytest.raises(ValueError, match=error):
        LocalMemory(**kwargs)