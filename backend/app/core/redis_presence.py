"""
Redis-backed WebSocket presence tracking.

Replaces the in-memory ConnectionManager dict with Redis hashes,
enabling multi-process scaling and surviving server restarts.

Key patterns:
  ws:room:{room_code}       → Hash[user_id → "1"]        (online users)
  ws:user:{user_id}         → String(room_code)           (reverse lookup)
  ws:room:{room_code}:count → String(count)               (fast count)
"""

from typing import Optional

from app.core.redis import redis_client


# ---------------------------------------------------------------------------
# Presence keys
# ---------------------------------------------------------------------------


def _room_key(room_code: str) -> str:
    return f"ws:room:{room_code}"


def _user_key(user_id: int) -> str:
    return f"ws:user:{user_id}"


def _count_key(room_code: str) -> str:
    return f"ws:room:{room_code}:count"


# ---------------------------------------------------------------------------
# Core presence operations
# ---------------------------------------------------------------------------


async def track_presence(
    room_code: str,
    user_id: int,
) -> None:
    """Mark a user as online in a room."""
    pipe = redis_client.pipeline()
    pipe.hset(_room_key(room_code), str(user_id), "1")
    pipe.set(_user_key(user_id), room_code)
    pipe.hlen(_room_key(room_code))
    results = await pipe.execute()

    count = results[2]
    await redis_client.set(_count_key(room_code), str(count))


async def remove_presence(
    room_code: str,
    user_id: int,
) -> None:
    """Mark a user as offline in a room."""
    pipe = redis_client.pipeline()
    pipe.hdel(_room_key(room_code), str(user_id))
    pipe.delete(_user_key(user_id))
    pipe.hlen(_room_key(room_code))
    results = await pipe.execute()

    count = results[2]
    if count == 0:
        await redis_client.delete(_count_key(room_code))
        await redis_client.delete(_room_key(room_code))
    else:
        await redis_client.set(_count_key(room_code), str(count))


async def is_online(
    room_code: str,
    user_id: int,
) -> bool:
    """Check if a user is online in a room."""
    return await redis_client.hexists(_room_key(room_code), str(user_id))


async def get_online_users(
    room_code: str,
) -> list[int]:
    """Return list of user IDs online in a room."""
    members = await redis_client.hkeys(_room_key(room_code))
    return [int(uid) for uid in members]


async def get_online_count(
    room_code: str,
) -> int:
    """Return the number of online users in a room."""
    count = await redis_client.get(_count_key(room_code))
    return int(count) if count else 0


async def get_user_room(
    user_id: int,
) -> Optional[str]:
    """Return the room code a user is connected to, or None."""
    return await redis_client.get(_user_key(user_id))


async def get_all_room_codes() -> list[str]:
    """Return all room codes with at least one online user."""
    keys = await redis_client.keys("ws:room:*:count")
    codes = []
    for key in keys:
        # key format: "ws:room:{room_code}:count"
        parts = key.split(":")
        if len(parts) >= 3:
            codes.append(parts[2])
    return codes
