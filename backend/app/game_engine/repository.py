from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.game_engine.models import Game, GamePlayer


async def get_by_room_id(
    db: AsyncSession,
    room_id: int,
) -> Optional[Game]:
    result = await db.execute(
        select(Game).where(
            Game.room_id == room_id
        )
    )

    return result.scalar_one_or_none()


async def create_game(
    db: AsyncSession,
    room_id: int,
    max_rounds: int = 1,
    phase_durations: dict | None = None,
) -> Game:
    game = Game(
        room_id=room_id,
        status="active",
        round_number=1,
        phase="role_assignment",
        max_rounds=max_rounds,
        phase_durations=phase_durations or {},
    )

    db.add(game)

    await db.flush()

    return game


async def add_game_player(
    db: AsyncSession,
    game_id: int,
    user_id: int,
    role: str,
) -> GamePlayer:
    game_player = GamePlayer(
        game_id=game_id,
        user_id=user_id,
        role=role,
        score=0,
    )

    db.add(game_player)

    await db.flush()

    return game_player

async def get_game_players(
    db: AsyncSession,
    game_id: int,
) -> list[GamePlayer]:
    result = await db.execute(
        select(GamePlayer)
        .where(
            GamePlayer.game_id == game_id
        )
        .order_by(
            GamePlayer.id.asc()
        )
    )

    return list(result.scalars().all())

async def get_game_player(
    db: AsyncSession,
    game_id: int,
    user_id: int,
) -> Optional[GamePlayer]:
    result = await db.execute(
        select(GamePlayer).where(
            GamePlayer.game_id == game_id,
            GamePlayer.user_id == user_id,
        )
    )

    return result.scalar_one_or_none()

async def get_by_id(
    db: AsyncSession,
    game_id: int,
) -> Optional[Game]:
    result = await db.execute(
        select(Game).where(
            Game.id == game_id
        )
    )

    return result.scalar_one_or_none()

async def get_player_by_role(
    db: AsyncSession,
    game_id: int,
    role: str,
) -> Optional[GamePlayer]:
    result = await db.execute(
        select(GamePlayer).where(
            GamePlayer.game_id == game_id,
            GamePlayer.role == role,
        )
    )

    return result.scalar_one_or_none()


async def get_game_players_for_user(
    db: AsyncSession,
    user_id: int,
) -> list[GamePlayer]:
    result = await db.execute(
        select(GamePlayer).where(
            GamePlayer.user_id == user_id
        )
    )

    return list(result.scalars().all())