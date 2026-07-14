from fastapi import WebSocket
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_access_token
from app.core.redis import is_token_revoked
from app.core.redis_rate_limit import is_rate_limited
from app.users.models import User
from app.users.repository import get_by_id
from app.rooms import repository as room_repository
from app.websocket.manager import manager
from app.game_engine import repository as game_repository
from app.chat import repository as chat_repository
from app.chat import reaction_repository
from app.users import repository as user_repository
from app.missions.service import evaluate_message_missions
from app.game_engine.service import check_win_condition, calculate_final_scores
from app.game_engine.state_machine import GamePhase
from app.missions import repository as mission_repository
from app.voting import service as voting_service
from app.voting import repository as vote_repository
from app.events import repository as event_repository
from app.training import repository as training_repository

# Allowed emoji reactions
ALLOWED_EMOJIS = {"👍", "👎", "❤️", "😂", "😮", "😢", "🔥", "👀", "🎯", "✅"}

# Phases where chat messages are allowed
CHAT_ALLOWED_PHASES = {
    GamePhase.ROLE_ASSIGNMENT.value,
    GamePhase.INTERACTION.value,
    GamePhase.DISCUSSION.value,
    GamePhase.RESULT.value,
    GamePhase.GAME_OVER.value,
}


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

        # Rate limit: 30 messages per minute per user
        if await is_rate_limited("chat_message", str(user_id)):
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": "Rate limit exceeded. Please wait before sending another message.",
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

        # Phase-specific validation: only allow chat during certain phases
        game_check = await game_repository.get_by_room_id(
            db,
            room_id=room.id,
        )
        if game_check is not None and game_check.phase not in CHAT_ALLOWED_PHASES:
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": f"Chat is not allowed during the {game_check.phase} phase",
                }
            )
            return

        # Extract reply_to_message_id if provided
        reply_to_message_id = message.get("reply_to_message_id")
        if reply_to_message_id is not None:
            if not isinstance(reply_to_message_id, int):
                reply_to_message_id = None

        updated_missions = []
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
                    reply_to_message_id=reply_to_message_id,
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

            if game is not None:
                await event_repository.create_event(
                    db=db,
                    game_id=game.id,
                    round_number=game.round_number,
                    event_type="message_sent",
                    user_id=user_id,
                    payload={
                        "message_id": chat_message.id,
                        "content": content.strip(),
                    },
                )

                # Store training data for ML
                game_player = await game_repository.get_game_player(
                    db,
                    game_id=game.id,
                    user_id=user_id,
                )
                if game_player is not None:
                    has_reply = reply_to_message_id is not None
                    reply_to_role = None
                    if has_reply:
                        replied_msg = await chat_repository.get_message_by_id(
                            db, reply_to_message_id,
                        )
                        if replied_msg is not None:
                            replied_player = (
                                await game_repository.get_game_player(
                                    db,
                                    game_id=game.id,
                                    user_id=replied_msg.user_id,
                                )
                            )
                            if replied_player is not None:
                                reply_to_role = replied_player.role

                    await training_repository.create_training_message(
                        db=db,
                        game_id=game.id,
                        user_id=user_id,
                        role=game_player.role,
                        phase=game.phase,
                        content=content.strip(),
                        round_number=game.round_number,
                        has_reply=has_reply,
                        reply_to_role=reply_to_role,
                    )

            # ------------------------------------------
            # Evaluate chat-driven missions during interaction.
            # ------------------------------------------

            if (
                game is not None
                and game.status == "active"
                and game.phase == GamePhase.INTERACTION.value
            ):
                updated_missions = (
                    await evaluate_message_missions(
                        db=db,
                        game_id=game.id,
                        sender_user_id=user_id,
                        content=content.strip(),
                        round_number=game.round_number,
                    )
                )

                for mission in updated_missions:
                    await event_repository.create_event(
                        db=db,
                        game_id=game.id,
                        round_number=game.round_number,
                        event_type="mission_progress",
                        user_id=mission.assigned_to_user_id,
                        payload={
                            "mission_id": mission.id,
                            "mission_type": mission.mission_type,
                            "current_value": mission.current_value,
                            "target_value": mission.target_value,
                            "status": mission.status,
                            "triggered_by_user_id": user_id,
                        },
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
                updated_missions
                and game is not None
            ):
                win_result = await check_win_condition(
                    db=db,
                    game_id=game.id,
                )

                if win_result.game_over:
                    scores = await calculate_final_scores(
                        db=db,
                        game_id=game.id,
                    )

                    game.status = "completed"
                    game.phase = "game_over"
                    room.status = "completed"

                    await event_repository.create_event(
                        db=db,
                        game_id=game.id,
                        round_number=game.round_number,
                        event_type="game_over",
                        payload={
                            "winner": win_result.winner,
                            "reason": win_result.reason,
                        },
                    )

                    await db.commit()
                    await db.refresh(game)
                    await db.refresh(room)

                    game_players = (
                        await game_repository.get_game_players(
                            db, game_id=game.id
                        )
                    )

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

        for updated_mission in updated_missions:
            await manager.send_to_user(
                room_code=room_code,
                user_id=updated_mission.assigned_to_user_id,
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
                    "reply_to_message_id": chat_message.reply_to_message_id,
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
            game_players = (
                await game_repository.get_game_players(
                    db, game_id=game.id
                )
            )

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
                    "scores": [
                        {
                            "user_id": gp.user_id,
                            "role": gp.role,
                            "score": gp.score,
                            "username": (
                                await get_by_id(db, gp.user_id)
                            ).username,
                        }
                        for gp in game_players
                    ],
                },
            )

            # Train ML model after game over
            try:
                from app.ml.service import train_model
                ml_result = await train_model(db=db)
                await manager.broadcast_to_room(
                    room_code=room_code,
                    message={
                        "type": "ML_TRAINED",
                        "accuracy": ml_result.get("accuracy"),
                        "samples_used": ml_result.get("samples_used"),
                    },
                )
            except Exception:
                pass  # ML training is non-critical

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

        # Rate limit: 5 votes per minute per user
        if await is_rate_limited("vote", str(user_id)):
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": "Rate limit exceeded. Please wait before voting again.",
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

            await event_repository.create_event(
                db=db,
                game_id=game.id,
                round_number=game.round_number,
                event_type="vote_cast",
                user_id=user_id,
                payload={
                    "target_user_id": target_user_id,
                },
            )

            await db.commit()

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

        # Check if all players have voted - auto advance to result
        game_players = await game_repository.get_game_players(
            db, game_id=game.id
        )
        total_players = len(game_players)
        
        votes = await vote_repository.get_votes_for_round(
            db=db,
            game_id=game.id,
            round_number=game.round_number,
        )
        unique_voters = len(set(v.voter_user_id for v in votes))
        
        if unique_voters >= total_players:
            # All players voted - auto advance to result
            game.phase = GamePhase.RESULT.value
            game.phase_started_at = None
            
            from app.game_engine.timer import cancel_timer
            cancel_timer(game.id)
            
            await event_repository.create_event(
                db=db,
                game_id=game.id,
                round_number=game.round_number,
                event_type="phase_changed",
                payload={
                    "from_phase": GamePhase.VOTING.value,
                    "to_phase": GamePhase.RESULT.value,
                    "auto": True,
                    "reason": "all_players_voted",
                },
            )
            
            await db.commit()
            
            # Get vote results with coordinator identification check
            vote_results = await voting_service.tally_votes(
                db=db,
                game_id=game.id,
                round_number=game.round_number,
            )
            
            await manager.broadcast_to_room(
                room_code=room_code,
                message={
                    "type": "VOTE_RESULTS",
                    "results": vote_results.model_dump(),
                },
            )
            
            await manager.broadcast_to_room(
                room_code=room_code,
                message={
                    "type": "PHASE_CHANGED",
                    "game": {
                        "id": game.id,
                        "phase": GamePhase.RESULT.value,
                        "round_number": game.round_number,
                    },
                },
            )
            
            # Check win condition based on vote result
            win_result = await check_win_condition(
                db=db,
                game_id=game.id,
            )
            if win_result.game_over:
                scores = await calculate_final_scores(
                    db=db,
                    game_id=game.id,
                )

                game_players = (
                    await game_repository.get_game_players(
                        db, game_id=game.id
                    )
                )
                game.status = "completed"
                game.phase = GamePhase.GAME_OVER.value
                room.status = "completed"
                await db.commit()
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
                        "scores": [
                            {
                                "user_id": gp.user_id,
                                "role": gp.role,
                                "score": gp.score,
                                "username": (
                                    await get_by_id(db, gp.user_id)
                                ).username,
                            }
                            for gp in game_players
                        ],
                    },
                )
                return
            
            # Start timer for result phase
            from app.game_engine.timer import start_phase_timer
            from app.db.session import SessionLocal
            start_phase_timer(
                db_factory=SessionLocal,
                game_id=game.id,
                room_code=room_code,
                phase=GamePhase.RESULT.value,
            )
        
        return

    # --------------------------------------------------
    # ADD_REACTION
    # --------------------------------------------------

    if event_type == "ADD_REACTION":
        payload = message.get("payload", {})
        message_id = payload.get("message_id")
        emoji = payload.get("emoji", "").strip()

        if not isinstance(message_id, int):
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": "ADD_REACTION requires payload.message_id as integer",
                }
            )
            return

        if not emoji or emoji not in ALLOWED_EMOJIS:
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": f"ADD_REACTION requires a valid emoji. Allowed: {', '.join(ALLOWED_EMOJIS)}",
                }
            )
            return

        # Rate limit: 30 reactions per minute
        if await is_rate_limited("chat_message", f"reaction:{user_id}"):
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": "Rate limit exceeded. Please wait before reacting again.",
                }
            )
            return

        room = await room_repository.get_by_code(db, room_code)
        if room is None:
            await websocket.send_json({"type": "ERROR", "message": "Room not found"})
            return

        # Verify message exists in this room
        msg = await chat_repository.get_message_by_id(db, message_id)
        if msg is None or msg.room_id != room.id:
            await websocket.send_json(
                {"type": "ERROR", "message": "Message not found in this room"}
            )
            return

        try:
            await reaction_repository.add_reaction(
                db=db,
                message_id=message_id,
                user_id=user_id,
                emoji=emoji,
            )

            # Store training data for ML — reactions are a social signal
            game = await game_repository.get_by_room_id(db, room_id=room.id)
            if game is not None and game.status == "active":
                game_player = await game_repository.get_game_player(
                    db, game_id=game.id, user_id=user_id,
                )
                if game_player is not None:
                    await training_repository.create_training_message(
                        db=db,
                        game_id=game.id,
                        user_id=user_id,
                        role=game_player.role,
                        phase=game.phase,
                        content=f"[reaction:{emoji}]",
                        round_number=game.round_number,
                    )

            await db.commit()

            # Get updated reaction counts
            reaction_counts = await reaction_repository.get_reaction_counts(
                db=db,
                message_id=message_id,
            )

            await manager.broadcast_to_room(
                room_code=room_code,
                message={
                    "type": "REACTION_ADDED",
                    "message_id": message_id,
                    "user_id": user_id,
                    "emoji": emoji,
                    "reactions": {
                        e: {"count": len(uids), "user_ids": uids}
                        for e, uids in reaction_counts.items()
                    },
                },
            )
        except Exception:
            await db.rollback()
            await websocket.send_json(
                {"type": "ERROR", "message": "Failed to add reaction"}
            )
        return

    # --------------------------------------------------
    # REMOVE_REACTION
    # --------------------------------------------------

    if event_type == "REMOVE_REACTION":
        payload = message.get("payload", {})
        message_id = payload.get("message_id")
        emoji = payload.get("emoji", "").strip()

        if not isinstance(message_id, int):
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "message": "REMOVE_REACTION requires payload.message_id as integer",
                }
            )
            return

        if not emoji:
            await websocket.send_json(
                {"type": "ERROR", "message": "REMOVE_REACTION requires payload.emoji"}
            )
            return

        room = await room_repository.get_by_code(db, room_code)
        if room is None:
            await websocket.send_json({"type": "ERROR", "message": "Room not found"})
            return

        try:
            removed = await reaction_repository.remove_reaction(
                db=db,
                message_id=message_id,
                user_id=user_id,
                emoji=emoji,
            )
            await db.commit()

            if removed:
                reaction_counts = await reaction_repository.get_reaction_counts(
                    db=db,
                    message_id=message_id,
                )

                await manager.broadcast_to_room(
                    room_code=room_code,
                    message={
                        "type": "REACTION_REMOVED",
                        "message_id": message_id,
                        "user_id": user_id,
                        "emoji": emoji,
                        "reactions": {
                            e: {"count": len(uids), "user_ids": uids}
                            for e, uids in reaction_counts.items()
                        },
                    },
                )
        except Exception:
            await db.rollback()
            await websocket.send_json(
                {"type": "ERROR", "message": "Failed to remove reaction"}
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

    # Check if token has been revoked (logout)
    jti = payload.get("jti")
    if jti and await is_token_revoked(jti):
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


async def send_chat_history_to_user(
    db: AsyncSession,
    websocket: WebSocket,
    room_code: str,
    limit: int = 100,
) -> None:
    room = await room_repository.get_by_code(
        db,
        room_code,
    )

    if room is None:
        return

    messages = await chat_repository.get_room_messages(
        db=db,
        room_id=room.id,
        limit=limit,
    )

    # Get all reactions for these messages
    message_ids = [message.id for message, _ in messages]
    all_reactions = await reaction_repository.get_reactions_for_messages(
        db=db,
        message_ids=message_ids,
    )

    # Group reactions by message_id
    reactions_by_message: dict[int, dict[str, list[int]]] = {}
    for reaction in all_reactions:
        if reaction.message_id not in reactions_by_message:
            reactions_by_message[reaction.message_id] = {}
        if reaction.emoji not in reactions_by_message[reaction.message_id]:
            reactions_by_message[reaction.message_id][reaction.emoji] = []
        reactions_by_message[reaction.message_id][reaction.emoji].append(reaction.user_id)

    await websocket.send_json(
        {
            "type": "CHAT_HISTORY",
            "messages": [
                {
                    "id": message.id,
                    "user_id": message.user_id,
                    "username": username,
                    "content": message.content,
                    "reply_to_message_id": message.reply_to_message_id,
                    "reactions": {
                        e: {"count": len(uids), "user_ids": uids}
                        for e, uids in reactions_by_message.get(message.id, {}).items()
                    },
                    "created_at": message.created_at.isoformat(),
                }
                for message, username in messages
            ],
        }
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
