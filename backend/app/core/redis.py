import redis.asyncio as redis

from app.core.config import settings


redis_client = redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)

OAUTH_STATE_TTL_SECONDS = 300


async def store_oauth_state(state: str) -> None:
    key = f"oauth_state:{state}"

    await redis_client.set(
        key,
        "1",
        ex=OAUTH_STATE_TTL_SECONDS,
    )


async def consume_oauth_state(state: str) -> bool:
    key = f"oauth_state:{state}"

    value = await redis_client.getdel(key)

    return value is not None


LINK_STATE_TTL_SECONDS = 300


async def store_google_link_state(
    state: str,
    user_id: int,
) -> None:
    key = f"google_link_state:{state}"

    await redis_client.set(
        key,
        str(user_id),
        ex=LINK_STATE_TTL_SECONDS,
    )


async def consume_google_link_state(
    state: str,
):
    key = f"google_link_state:{state}"

    value = await redis_client.getdel(key)

    if value is None:
        return None

    return int(value)