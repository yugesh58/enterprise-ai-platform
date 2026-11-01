import hashlib
import hmac
import time
from uuid import uuid4

import redis
from fastapi import (
    Depends,
    HTTPException,
    Response,
    Security,
    status,
)

from app.api.dependencies.security import (
    api_key_header,
    require_api_key,
)
from app.core.config import settings
from app.storage.redis_client import get_redis_client

SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local now_ms = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]

redis.call(
    'ZREMRANGEBYSCORE',
    key,
    '-inf',
    now_ms - window_ms
)

local count = redis.call('ZCARD', key)

if count >= limit then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = 1

    if oldest[2] then
        retry_after = math.max(
            1,
            math.ceil((tonumber(oldest[2]) + window_ms - now_ms) / 1000)
        )
    end

    redis.call('PEXPIRE', key, window_ms)
    return {0, retry_after, count}
end

redis.call('ZADD', key, now_ms, member)
redis.call('PEXPIRE', key, window_ms)

return {1, 0, count + 1}
"""


def enforce_rate_limit(
    response: Response,
    api_key: str | None = Security(api_key_header),
    _authenticated: None = Depends(require_api_key),
) -> None:
    """Enforce a shared sliding-window limit for an authenticated API key."""

    if not settings.RATE_LIMIT_ENABLED:
        return

    if (
        not settings.RATE_LIMIT_KEY_SECRET
        or settings.RATE_LIMIT_REQUESTS < 1
        or settings.RATE_LIMIT_WINDOW_SECONDS < 1
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting is not configured correctly.",
        )

    if not api_key:
        # Normally handled by require_api_key.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )

    client_id = hmac.new(
        settings.RATE_LIMIT_KEY_SECRET.encode("utf-8"),
        api_key.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    redis_key = f"rate-limit:{client_id}"
    now_ms = time.time_ns() // 1_000_000
    window_ms = settings.RATE_LIMIT_WINDOW_SECONDS * 1000
    member = f"{now_ms}:{uuid4().hex}"

    try:
        result = get_redis_client().eval(
            SLIDING_WINDOW_SCRIPT,
            1,
            redis_key,
            now_ms,
            window_ms,
            settings.RATE_LIMIT_REQUESTS,
            member,
        )
    except redis.RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting service is unavailable.",
        ) from exc

    allowed, retry_after, count = map(int, result)

    response.headers["X-RateLimit-Limit"] = str(
    settings.RATE_LIMIT_REQUESTS
)

    response.headers["X-RateLimit-Remaining"] = str(
        max(0, settings.RATE_LIMIT_REQUESTS - count)
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(settings.RATE_LIMIT_REQUESTS),
                "X-RateLimit-Remaining": "0",
                },
             )
