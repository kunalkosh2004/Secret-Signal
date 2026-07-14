import secrets
import string

from sqlalchemy.ext.asyncio import AsyncSession

from app.rooms import repository as room_repository
from app.rooms.models import Room
from app.rooms.schemas import CreateRoomRequest, GameSettings

ROOM_CODE_LENGTH = 6

ROOM_CODE_ALPHABET = string.ascii_uppercase + string.digits


def _generate_room_code() -> str:
    return "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(ROOM_CODE_LENGTH))


async def create_room(
    db: AsyncSession,
    host_id: int,
    request: CreateRoomRequest,
) -> Room:
    while True:
        code = _generate_room_code()

        existing_room = await room_repository.get_by_code(
            db,
            code,
        )

        if existing_room is None:
            break

    game_settings = GameSettings(**request.settings)

    room = await room_repository.create(
        db,
        code=code,
        host_id=host_id,
        status="waiting",
        max_players=request.max_players,
        settings=game_settings.model_dump(),
    )

    await room_repository.add_player(
        db,
        room_id=room.id,
        user_id=host_id,
    )

    return room


async def join_room(
    db: AsyncSession,
    code: str,
    user_id: int,
) -> Room:
    room = await room_repository.get_by_code(
        db,
        code,
    )

    if room is None:
        raise ValueError("Room not found")

    if room.status != "waiting":
        raise ValueError("Room is not open for joining")

    existing_player = await room_repository.get_player(
        db,
        room_id=room.id,
        user_id=user_id,
    )

    if existing_player is not None:
        raise ValueError("User is already in this room")

    player_count = await room_repository.count_players(
        db,
        room_id=room.id,
    )

    if player_count >= room.max_players:
        raise ValueError("Room is full")

    await room_repository.add_player(
        db,
        room_id=room.id,
        user_id=user_id,
    )

    return room


async def leave_room(
    db: AsyncSession,
    code: str,
    user_id: int,
) -> Room:
    room = await room_repository.get_by_code(
        db,
        code,
    )

    if room is None:
        raise ValueError("Room not found")

    membership = await room_repository.get_player(
        db,
        room_id=room.id,
        user_id=user_id,
    )

    if membership is None:
        raise ValueError("User is not in this room")

    if room.host_id == user_id:
        raise ValueError(
            "Host cannot leave the room without closing or transferring it"
        )

    await room_repository.remove_player(
        db,
        room_id=room.id,
        user_id=user_id,
    )

    return room
