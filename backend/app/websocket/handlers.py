from fastapi import WebSocket
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_access_token
from app.users.models import User
from app.users.repository import get_by_id
from app.rooms import repository as room_repository
from app.websocket.manager import manager
from app.game_engine import repository as game_repository
from app.chat import repository as chat_repository
from app.users import repository as user_repository


async def handle_message(
    db: AsyncSession,
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

    if event_type == "PLAYER_READY":
        ready = message.get("payload", {}).get(
            "ready"
        )

        if not isinstance(ready, bool):
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": (
                        "PLAYER_READY requires "
                        "payload.ready as boolean"
                    ),
                }
            )
            return

        room = await room_repository.get_by_code(
            db,
            room_code,
        )

        if room is None:
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": "Room not found",
                }
            )
            return

        await room_repository.set_player_ready(
            db,
            room_id=room.id,
            user_id=user_id,
            is_ready=ready,
        )

        await broadcast_room_state(
            db=db,
            room_code=room_code,
        )

        return

    if event_type == "SEND_MESSAGE":
        content = message.get("content", "")

        if not content or not content.strip():
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": "SEND_MESSAGE requires non-empty content",
                }
            )
            return

        room = await room_repository.get_by_code(db, room_code)

        if room is None:
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": "Room not found",
                }
            )
            return

        chat_message = await chat_repository.create_message(
            db,
            room_id=room.id,
            user_id=user_id,
            content=content.strip(),
        )

        sender = await user_repository.get_by_id(db, user_id)
        username = sender.username if sender else str(user_id)

        await manager.broadcast_to_room(
            room_code=room_code,
            message={
                "type": "MESSAGE_SENT",
                "message": {
                    "id": chat_message.id,
                    "user_id": user_id,
                    "username": username,
                    "content": content.strip(),
                    "created_at": chat_message.created_at.isoformat(),
                },
            },
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

    players = await room_repository.get_players_with_ready_state(
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
                "is_ready": is_ready,
            }
            for player, is_ready in players
        ],
    }

    await manager.broadcast_to_room(
        room_code=room_code,
        message=message,
    )

async def send_game_state_to_user(
    db: AsyncSession,
    websocket: WebSocket,
    room_code: str,
    user_id: int,
) -> None:
    room = await room_repository.get_by_code(
        db,
        room_code,
    )

    if room is None:
        return

    if room.status != "in_game":
        return

    game = await game_repository.get_by_room_id(
        db,
        room_id=room.id,
    )

    if game is None:
        return

    game_player = await game_repository.get_game_player(
        db,
        game_id=game.id,
        user_id=user_id,
    )

    if game_player is None:
        return

    await websocket.send_json(
        {
            "type": "GAME_STATE",
            "game": {
                "id": game.id,
                "status": game.status,
                "round_number": game.round_number,
                "phase": game.phase,
            },
        }
    )

    await websocket.send_json(
        {
            "type": "ROLE_ASSIGNMENT",
            "game_id": game.id,
            "role": game_player.role,
            "score": game_player.score,
        }
    )