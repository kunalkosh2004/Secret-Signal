"""
Redis-based rate limiting using sliding window counters.

Key patterns:
  ratelimit:{scope}:{identifier}   → Sorted set of timestamps
"""

import time
from typing import Optional

from app.core.redis import redis_client


# Default limits: (max_requests, window_seconds)
DEFAULT_LIMITS = {
    "chat_message": (30, 60),  # 30 messages per minute
    "vote": (5, 60),  # 5 votes per minute
    "api_auth": (10, 60),  # 10 auth attempts per minute
    "api_general": (100, 60),  # 100 API calls per minute
    "ws_connect": (20, 60),  # 20 WS connections per minute
}


def _key(scope: str, identifier: str) -> str:
    return f"ratelimit:{scope}:{identifier}"


async def check_rate_limit(
    scope: str,
    identifier: str,
    max_requests: Optional[int] = None,
    window_seconds: Optional[int] = None,
) -> tuple[bool, int]:
    """
    Check if an action is within rate limits.

    Returns (allowed, remaining).
    - allowed: True if the action is permitted
    - remaining: number of remaining requests in the window
    """
    if max_requests is None or window_seconds is None:
        defaults = DEFAULT_LIMITS.get(scope, (100, 60))
        if max_requests is None:
            max_requests = defaults[0]
        if window_seconds is None:
            window_seconds = defaults[1]

    key = _key(scope, identifier)
    now = time.time()
    window_start = now - window_seconds

    pipe = redis_client.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window_seconds)
    results = await pipe.execute()

    count = results[2]
    remaining = max(0, max_requests - count)

    return count <= max_requests, remaining


async def is_rate_limited(
    scope: str,
    identifier: str,
    max_requests: Optional[int] = None,
    window_seconds: Optional[int] = None,
) -> bool:
    """Return True if the action should be blocked."""
    allowed, _ = await check_rate_limit(scope, identifier, max_requests, window_seconds)
    return not allowed


async def get_rate_limit_info(
    scope: str,
    identifier: str,
    max_requests: Optional[int] = None,
    window_seconds: Optional[int] = None,
) -> dict:
    """Return full rate limit info for headers."""
    if max_requests is None or window_seconds is None:
        defaults = DEFAULT_LIMITS.get(scope, (100, 60))
        if max_requests is None:
            max_requests = defaults[0]
        if window_seconds is None:
            window_seconds = defaults[1]

    allowed, remaining = await check_rate_limit(
        scope, identifier, max_requests, window_seconds
    )
    return {
        "allowed": allowed,
        "remaining": remaining,
        "limit": max_requests,
        "window": window_seconds,
    }


async def reset_rate_limit(scope: str, identifier: str) -> None:
    """Reset rate limit for a specific scope+identifier."""
    await redis_client.delete(_key(scope, identifier))
