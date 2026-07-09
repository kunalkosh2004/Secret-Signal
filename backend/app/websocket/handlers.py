from fastapi import WebSocket
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_access_token
from app.users.models import User
from app.users.repository import get_by_id
from app.rooms import repository as room_repository
from app.websocket.manager import manager


async def handle_message(
    websocket: WebSocket,
    room_code: str,
    user_id: int,
    message: dict,
) -> None:
    event_type = message.get("type")

    if event_type is None:
        await websocket.send_json(
            {
                "type": "ERROR",
                "message": "Missing event type",
            }
        )
        return

    await websocket.send_json(
        {
            "type": "ERROR",
            "message": f"Unknown event type: {event_type}",
        }
    )

async def authenticate_websocket(
    db: AsyncSession,
    token: str,
) -> Optional[User]:
    payload = decode_access_token(token)

    if payload is None:
        return None

    user_id = payload.get("sub")

    if user_id is None:
        return None

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return None

    user = await get_by_id(
        db,
        user_id,
    )

    return user

async def authorize_room_connection(
    db: AsyncSession,
    room_code: str,
    user_id: int,
) -> bool:
    room = await room_repository.get_by_code(
        db,
        room_code,
    )

    if room is None:
        return False

    membership = await room_repository.get_player(
        db,
        room_id=room.id,
        user_id=user_id,
    )

    return membership is not None

async def broadcast_room_state(
    db: AsyncSession,
    room_code: str,
) -> None:
    room = await room_repository.get_by_code(
        db,
        room_code,
    )

    if room is None:
        return

    players = await room_repository.get_players(
        db,
        room_id=room.id,
    )

    message = {
        "type": "ROOM_STATE",
        "room": {
            "id": room.id,
            "code": room.code,
            "host_id": room.host_id,
            "status": room.status,
            "max_players": room.max_players,
            "settings": room.settings,
        },
        "players": [
            {
                "id": player.id,
                "username": player.username,
            }
            for player in players
        ],
    }

    await manager.broadcast_to_room(
        room_code=room_code,
        message=message,
    )