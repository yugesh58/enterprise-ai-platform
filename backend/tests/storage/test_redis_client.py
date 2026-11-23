from unittest.mock import Mock

from app.storage import redis_client


def test_dispose_closes_client_and_clears_cache(monkeypatch):
    redis_client.get_redis_client.cache_clear()

    mock_client = Mock()

    monkeypatch.setattr(
        redis_client.redis,
        "Redis",
        lambda **kwargs: mock_client,
    )

    client = redis_client.get_redis_client()

    assert client is mock_client
    assert redis_client.get_redis_client.cache_info().currsize == 1

    redis_client.dispose_redis_client()

    mock_client.close.assert_called_once()
    assert redis_client.get_redis_client.cache_info().currsize == 0


def test_dispose_without_initialized_client():
    redis_client.get_redis_client.cache_clear()

    redis_client.dispose_redis_client()

    assert redis_client.get_redis_client.cache_info().currsize == 0