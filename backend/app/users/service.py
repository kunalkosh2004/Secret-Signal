"""
User service — business logic layer for user operations.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.users import repository as user_repository
from app.users.models import User
from app.users.schemas import UserResponse


async def get_user_by_id(
    db: AsyncSession,
    user_id: int,
) -> Optional[User]:
    return await user_repository.get_by_id(db, user_id)


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> Optional[User]:
    return await user_repository.get_by_email(db, email)


async def get_user_by_username(
    db: AsyncSession,
    username: str,
) -> Optional[User]:
    return await user_repository.get_by_username(db, username)


async def update_username(
    db: AsyncSession,
    user: User,
    new_username: str,
) -> User:
    existing = await user_repository.get_by_username(
        db, new_username
    )

    if existing is not None and existing.id != user.id:
        raise ValueError("Username is already taken")

    updated = await user_repository.update(
        db,
        user=user,
        username=new_username,
    )

    await db.commit()
    await db.refresh(updated)

    return updated


async def get_user_stats(
    db: AsyncSession,
    user_id: int,
) -> dict:
    from app.game_engine import repository as game_repository

    user = await user_repository.get_by_id(db, user_id)

    if user is None:
        raise ValueError("User not found")

    game_players = await game_repository.get_game_players_for_user(
        db, user_id=user_id
    )

    games_played = len(game_players)
    total_score = sum(gp.score for gp in game_players)
    wins = sum(
        1 for gp in game_players
        if gp.role == "coordinator" and gp.score > 0
        or gp.role != "coordinator" and gp.score > 0
    )

    return {
        "user": UserResponse.model_validate(user),
        "games_played": games_played,
        "total_score": total_score,
        "wins": wins,
    }
