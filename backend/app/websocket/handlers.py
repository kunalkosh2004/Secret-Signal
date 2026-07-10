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
from app.missions.service import increment_mission_progress
from app.game_engine.service import check_win_condition
from app.game_engine.state_machine import GamePhase
from app.missions import repository as mission_repository
from app.voting import service as voting_service


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

    # --------------------------------------------------
    # PLAYER_READY
    # --------------------------------------------------

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
        
        if room.status != "waiting":
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": (
                        "Ready status can only be changed "
                        "while the room is waiting"
                    ),
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

    # --------------------------------------------------
    # SEND_MESSAGE
    # --------------------------------------------------

    if event_type == "SEND_MESSAGE":
        content = message.get("content", "")

        if not content or not content.strip():
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": (
                        "SEND_MESSAGE requires "
                        "non-empty content"
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

        updated_mission = None
        win_result = None
        game = None

        try:
            # ------------------------------------------
            # Create chat message
            # ------------------------------------------

            chat_message = (
                await chat_repository.create_message(
                    db,
                    room_id=room.id,
                    user_id=user_id,
                    content=content.strip(),
                )
            )

            # ------------------------------------------
            # Load active game
            # ------------------------------------------

            game = await game_repository.get_by_room_id(
                db,
                room_id=room.id,
            )

            if game is not None and game.status == "completed":
                await db.rollback()

                await websocket.send_json(
                    {
                        "type": "ERROR",
                        "message": "Game has already ended",
                    }
                )
                return

            # ------------------------------------------
            # Progress send_messages mission (active game only)
            # ------------------------------------------

            if (
                game is not None
                and game.status == "active"
            ):
                updated_mission = (
                    await increment_mission_progress(
                        db=db,
                        game_id=game.id,
                        user_id=user_id,
                        mission_type="send_messages",
                        round_number=game.round_number,
                    )
                )

            # ------------------------------------------
            # Commit chat + mission progress
            # ------------------------------------------

            await db.commit()
            await db.refresh(chat_message)

            # ------------------------------------------
            # Check victory condition
            # ------------------------------------------

            if (
                updated_mission is not None
                and game is not None
            ):
                win_result = await check_win_condition(
                    db=db,
                    game_id=game.id,
                )

                if win_result.game_over:
                    game.status = "completed"
                    game.phase = "game_over"
                    room.status = "completed"

                    await db.commit()
                    await db.refresh(game)
                    await db.refresh(room)

        except Exception:
            await db.rollback()

            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": "Failed to send message",
                }
            )
            return

        # --------------------------------------------------
        # PRIVATE MISSION PROGRESS EVENT
        # --------------------------------------------------

        if updated_mission is not None:
            await manager.send_to_user(
                room_code=room_code,
                user_id=user_id,
                message={
                    "type": "MISSION_PROGRESS",
                    "mission": {
                        "id": updated_mission.id,
                        "current_value": (
                            updated_mission.current_value
                        ),
                        "target_value": (
                            updated_mission.target_value
                        ),
                        "status": updated_mission.status,
                    },
                },
            )

        # --------------------------------------------------
        # PUBLIC CHAT EVENT
        # --------------------------------------------------

        sender = await user_repository.get_by_id(
            db,
            user_id,
        )

        username = (
            sender.username
            if sender
            else str(user_id)
        )

        await manager.broadcast_to_room(
            room_code=room_code,
            message={
                "type": "MESSAGE_SENT",
                "message": {
                    "id": chat_message.id,
                    "user_id": user_id,
                    "username": username,
                    "content": content.strip(),
                    "created_at": (
                        chat_message.created_at.isoformat()
                    ),
                },
            },
        )

        # --------------------------------------------------
        # GAME OVER EVENT
        # --------------------------------------------------

        if (
            win_result is not None
            and win_result.game_over
            and game is not None
        ):
            await manager.broadcast_to_room(
                room_code=room_code,
                message={
                    "type": "GAME_OVER",
                    "game": {
                        "id": game.id,
                        "status": game.status,
                        "round_number": game.round_number,
                        "phase": game.phase,
                    },
                    "winner": win_result.winner,
                    "reason": win_result.reason,
                },
            )

        return

    # --------------------------------------------------
    # CAST_VOTE
    # --------------------------------------------------

    if event_type == "CAST_VOTE":
        target_user_id = message.get("payload", {}).get(
            "target_user_id"
        )

        if not isinstance(target_user_id, int):
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": (
                        "CAST_VOTE requires "
                        "payload.target_user_id as integer"
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

        game = await game_repository.get_by_room_id(
            db,
            room_id=room.id,
        )

        if game is None or game.status != "active":
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": "No active game in this room",
                }
            )
            return

        if game.phase != GamePhase.VOTING.value:
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": "Voting is not open in the current phase",
                }
            )
            return

        try:
            await voting_service.cast_vote(
                db=db,
                game_id=game.id,
                round_number=game.round_number,
                voter_user_id=user_id,
                target_user_id=target_user_id,
            )

        except ValueError as exc:
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": str(exc),
                }
            )
            return

        await websocket.send_json(
            {
                "type": "VOTE_CAST",
                "target_user_id": target_user_id,
            }
        )

        return

    # --------------------------------------------------
    # UNKNOWN EVENT
    # --------------------------------------------------

    await websocket.send_json(
        {
            "type": "ERROR",
            "message": (
                f"Unknown event type: {event_type}"
            ),
        }
    )

async def authenticate_websocket(
    db: AsyncSession,
    token: str,
) -> tuple[Optional[User], int | None]:
    payload = decode_access_token(token)

    if payload is None:
        return None, None

    user_id_str = payload.get("sub")

    if user_id_str is None:
        return None, None

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        return None, None

    user = await get_by_id(
        db,
        user_id,
    )

    return user, user_id

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
    try:
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

        if game_player.role == "coordinator":
            missions = await mission_repository.get_user_missions(
                db=db,
                game_id=game.id,
                user_id=user_id,
                round_number=game.round_number,
            )

            await websocket.send_json(
                {
                    "type": "MISSION_ASSIGNMENT",
                    "game_id": game.id,
                    "missions": [
                        {
                            "id": mission.id,
                            "mission_type": mission.mission_type,
                            "title": mission.title,
                            "description": mission.description,
                            "target_value": mission.target_value,
                            "current_value": mission.current_value,
                            "status": mission.status,
                            "round_number": mission.round_number,
                        }
                        for mission in missions
                    ],
                }
            )
    except RuntimeError:
        pass