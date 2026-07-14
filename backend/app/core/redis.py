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


# ---------------------------------------------------------------------------
# JWT token revocation (logout)
# ---------------------------------------------------------------------------

TOKEN_BLACKLIST_PREFIX = "token:blacklist:"


async def revoke_token(jti: str, expires_in_seconds: int) -> None:
    """
    Blacklist a JWT by its jti claim.
    The key expires automatically after the token's remaining TTL.
    """
    key = f"{TOKEN_BLACKLIST_PREFIX}{jti}"
    await redis_client.set(key, "1", ex=expires_in_seconds)


async def is_token_revoked(jti: str) -> bool:
    """Check if a JWT has been revoked (logged out)."""
    key = f"{TOKEN_BLACKLIST_PREFIX}{jti}"
    return await redis_client.exists(key) > 0


async def revoke_all_user_tokens(user_id: int, expires_in_seconds: int) -> None:
    """
    Mark all tokens for a user as revoked.
    Uses a separate key since we can't enumerate all jti values.
    """
    key = f"token:blacklist:user:{user_id}"
    await redis_client.set(key, "1", ex=expires_in_seconds)


async def is_user_token_revoked(user_id: int) -> bool:
    """Check if all tokens for a user have been revoked."""
    key = f"token:blacklist:user:{user_id}"
    return await redis_client.exists(key) > 0


# ---------------------------------------------------------------------------
# Password reset tokens
# ---------------------------------------------------------------------------

PASSWORD_RESET_PREFIX = "password_reset:"
PASSWORD_RESET_TTL = 3600  # 1 hour


async def store_password_reset_token(
    user_id: int,
    token: str,
) -> None:
    """Store a password reset token mapped to a user ID."""
    key = f"{PASSWORD_RESET_PREFIX}{token}"
    await redis_client.set(key, str(user_id), ex=PASSWORD_RESET_TTL)


async def consume_password_reset_token(token: str) -> int | None:
    """
    Consume a password reset token.
    Returns the user ID if valid, None otherwise.
    """
    key = f"{PASSWORD_RESET_PREFIX}{token}"
    value = await redis_client.getdel(key)
    return int(value) if value else None
