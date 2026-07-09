from typing import Optional

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.rooms.models import Room, RoomPlayer
from app.users.models import User


async def get_by_code(
    db: AsyncSession,
    code: str,
) -> Optional[Room]:
    result = await db.execute(
        select(Room).where(Room.code == code)
    )

    return result.scalar_one_or_none()

async def create(
    db: AsyncSession,
    **kwargs,
) -> Room:
    room = Room(**kwargs)

    db.add(room)

    await db.commit()
    await db.refresh(room)

    return room

async def add_player(
    db: AsyncSession,
    room_id: int,
    user_id: int,
) -> RoomPlayer:
    room_player = RoomPlayer(
        room_id=room_id,
        user_id=user_id,
    )

    db.add(room_player)

    await db.commit()
    await db.refresh(room_player)

    return room_player

async def remove_player(
    db: AsyncSession,
    room_id: int,
    user_id: int,
) -> None:
    await db.execute(
        delete(RoomPlayer).where(
            RoomPlayer.room_id == room_id,
            RoomPlayer.user_id == user_id,
        )
    )

    await db.commit()

async def get_player(
    db: AsyncSession,
    room_id: int,
    user_id: int,
) -> Optional[RoomPlayer]:
    result = await db.execute(
        select(RoomPlayer).where(
            RoomPlayer.room_id == room_id,
            RoomPlayer.user_id == user_id,
        )
    )

    return result.scalar_one_or_none()

async def count_players(
    db: AsyncSession,
    room_id: int,
) -> int:
    result = await db.execute(
        select(func.count(RoomPlayer.id)).where(
            RoomPlayer.room_id == room_id
        )
    )

    return result.scalar_one()

async def get_players(
    db: AsyncSession,
    room_id: int,
) -> list[User]:
    result = await db.execute(
        select(User)
        .join(
            RoomPlayer,
            RoomPlayer.user_id == User.id,
        )
        .where(
            RoomPlayer.room_id == room_id
        )
        .order_by(
            RoomPlayer.joined_at.asc()
        )
    )

    return list(result.scalars().all())

async def set_player_ready(
    db: AsyncSession,
    room_id: int,
    user_id: int,
    is_ready: bool,
) -> RoomPlayer:
    player = await get_player(
        db,
        room_id=room_id,
        user_id=user_id,
    )

    if player is None:
        raise ValueError(
            "User is not in this room"
        )

    player.is_ready = is_ready

    await db.commit()
    await db.refresh(player)

    return player

async def get_players_with_ready_state(
    db: AsyncSession,
    room_id: int,
) -> list[tuple[User, bool]]:
    result = await db.execute(
        select(
            User,
            RoomPlayer.is_ready,
        )
        .join(
            RoomPlayer,
            RoomPlayer.user_id == User.id,
        )
        .where(
            RoomPlayer.room_id == room_id
        )
        .order_by(
            RoomPlayer.joined_at.asc()
        )
    )

    return list(result.all())

async def get_by_id(
    db: AsyncSession,
    room_id: int,
) -> Optional[Room]:
    result = await db.execute(
        select(Room).where(
            Room.id == room_id
        )
    )

    return result.scalar_one_or_none()
