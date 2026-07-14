"""
Redis-based game state caching.

Caches frequently-read, rarely-written game state to reduce
PostgreSQL round-trips on every WebSocket message.

Key patterns:
  cache:room:{room_code}:info       → JSON{room data}
  cache:game:{game_id}:state        → JSON{game state}
  cache:game:{game_id}:players      → JSON[{player data}]
  cache:game:{game_id}:roles        → JSON{user_id → role}
"""

import json
from typing import Optional

from app.core.redis import redis_client


CACHE_TTL = 30  # seconds


def _room_info_key(room_code: str) -> str:
    return f"cache:room:{room_code}:info"


def _game_state_key(game_id: int) -> str:
    return f"cache:game:{game_id}:state"


def _game_players_key(game_id: int) -> str:
    return f"cache:game:{game_id}:players"


def _game_roles_key(game_id: int) -> str:
    return f"cache:game:{game_id}:roles"


async def cache_room_info(
    room_code: str,
    room_id: int,
    host_id: int,
    status: str,
    max_players: int,
    settings: Optional[dict] = None,
) -> None:
    """Cache room metadata."""
    data = {
        "room_id": room_id,
        "host_id": host_id,
        "status": status,
        "max_players": max_players,
        "settings": settings or {},
    }
    await redis_client.set(
        _room_info_key(room_code),
        json.dumps(data),
        ex=CACHE_TTL,
    )


async def get_cached_room_info(room_code: str) -> Optional[dict]:
    """Get cached room metadata."""
    raw = await redis_client.get(_room_info_key(room_code))
    return json.loads(raw) if raw else None


async def invalidate_room_info(room_code: str) -> None:
    """Invalidate cached room metadata."""
    await redis_client.delete(_room_info_key(room_code))


async def cache_game_state(
    game_id: int,
    status: str,
    phase: str,
    round_number: int,
) -> None:
    """Cache current game state."""
    data = {
        "status": status,
        "phase": phase,
        "round_number": round_number,
    }
    await redis_client.set(
        _game_state_key(game_id),
        json.dumps(data),
        ex=CACHE_TTL,
    )


async def get_cached_game_state(game_id: int) -> Optional[dict]:
    """Get cached game state."""
    raw = await redis_client.get(_game_state_key(game_id))
    return json.loads(raw) if raw else None


async def cache_game_roles(
    game_id: int,
    roles: dict[int, str],
) -> None:
    """Cache player role assignments (private to game)."""
    data = {str(uid): role for uid, role in roles.items()}
    await redis_client.set(
        _game_roles_key(game_id),
        json.dumps(data),
        ex=CACHE_TTL * 10,  # roles don't change, cache longer
    )


async def get_cached_game_roles(game_id: int) -> Optional[dict[int, str]]:
    """Get cached player roles."""
    raw = await redis_client.get(_game_roles_key(game_id))
    if raw is None:
        return None
    data = json.loads(raw)
    return {int(uid): role for uid, role in data.items()}


async def cache_game_players(
    game_id: int,
    players: list[dict],
) -> None:
    """Cache game player list."""
    await redis_client.set(
        _game_players_key(game_id),
        json.dumps(players),
        ex=CACHE_TTL,
    )


async def get_cached_game_players(game_id: int) -> Optional[list[dict]]:
    """Get cached game players."""
    raw = await redis_client.get(_game_players_key(game_id))
    return json.loads(raw) if raw else None


async def invalidate_game_cache(game_id: int) -> None:
    """Invalidate all cached data for a game."""
    pipe = redis_client.pipeline()
    pipe.delete(_game_state_key(game_id))
    pipe.delete(_game_players_key(game_id))
    pipe.delete(_game_roles_key(game_id))
    await pipe.execute()


async def invalidate_room_caches(room_code: str, game_id: Optional[int] = None) -> None:
    """Invalidate all caches for a room."""
    await invalidate_room_info(room_code)
    if game_id:
        await invalidate_game_cache(game_id)
