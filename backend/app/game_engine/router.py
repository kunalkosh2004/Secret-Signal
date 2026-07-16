from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
import asyncio

from app.auth.dependencies import get_current_user
from app.db.session import get_db, SessionLocal
from app.game_engine.schemas import (
    AdvancePhaseRequest,
    GameState,
)
from app.game_engine.service import (
    advance_phase as advance_phase_service,
    start_game as start_game_service,
    check_win_condition,
    calculate_final_scores,
)
from app.users.models import User
from app.users.repository import get_by_id as get_user_by_id
from app.game_engine import repository as game_repository
from app.rooms import repository as room_repository
from app.websocket.manager import manager
from app.missions import repository as mission_repository
from app.voting import service as voting_service
from app.game_engine.state_machine import GamePhase
from app.game_engine.timer import start_phase_timer, cancel_timer, get_phase_duration


router = APIRouter(
    prefix="/api/v1/games",
    tags=["games"],
)


@router.post(
    "/{room_code}/start",
    response_model=GameState,
    status_code=201,
)
async def start_game(
    room_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        normalized_room_code = room_code.strip().upper()

        game = await start_game_service(
            db=db,
            room_code=normalized_room_code,
            requester_id=current_user.id,
        )

        # Set phase_started_at for role_assignment phase
        game.phase_started_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(game)

        await manager.broadcast_to_room(
            room_code=normalized_room_code,
            message={
                "type": "GAME_START",
                "game": {
                    "id": game.id,
                    "room_id": game.room_id,
                    "status": game.status,
                    "round_number": game.round_number,
                    "max_rounds": game.max_rounds,
                    "phase": game.phase,
                },
            },
        )

        # Send timer info
        game_durations = game.phase_durations or {}
        duration = get_phase_duration(game.phase, game_durations)
        if duration:
            await manager.broadcast_to_room(
                room_code=normalized_room_code,
                message={
                    "type": "TIMER_UPDATED",
                    "phase": game.phase,
                    "duration_seconds": duration,
                    "ends_at": (
                        datetime.now(timezone.utc) + timedelta(seconds=duration)
                    ).isoformat(),
                },
            )

        # Start auto timer for role_assignment phase
        start_phase_timer(
            db_factory=SessionLocal,
            game_id=game.id,
            room_code=normalized_room_code,
            phase=game.phase,
            phase_durations=game_durations,
        )

        return game

    except ValueError as exc:
        message = str(exc)

        status_code = 400

        if message == "Room not found":
            status_code = 404

        elif message == "Only the room host can start the game":
            status_code = 403

        elif message == "A game has already been created for this room":
            status_code = 409

        raise HTTPException(
            status_code=status_code,
            detail=message,
        )


@router.post(
    "/{game_id}/advance-phase",
    response_model=GameState,
)
async def advance_phase(
    game_id: int,
    request: AdvancePhaseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    game = await game_repository.get_by_id(
        db,
        game_id=game_id,
    )

    if game is None:
        raise HTTPException(
            status_code=404,
            detail="Game not found",
        )

    room = await room_repository.get_by_id(
        db,
        room_id=game.room_id,
    )

    if room is None:
        raise HTTPException(
            status_code=404,
            detail="Room not found",
        )

    # Cancel existing timer
    cancel_timer(game_id)

    try:
        game = await advance_phase_service(
            db=db,
            game_id=game_id,
            next_phase=request.next_phase,
        )

        # Set phase_started_at for new phase
        game.phase_started_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(game)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    # --------------------------------------------------
    # BROADCAST PHASE CHANGE + START TIMER
    # --------------------------------------------------

    await manager.broadcast_to_room(
        room_code=room.code,
        message={
            "type": "PHASE_CHANGED",
            "game": {
                "id": game.id,
                "status": game.status,
                "round_number": game.round_number,
                "phase": game.phase,
            },
        },
    )

    # Send timer info
    game_durations = game.phase_durations or {}
    duration = get_phase_duration(game.phase, game_durations)
    if duration:
        await manager.broadcast_to_room(
            room_code=room.code,
            message={
                "type": "TIMER_UPDATED",
                "phase": game.phase,
                "duration_seconds": duration,
                "ends_at": (
                    datetime.now(timezone.utc) + timedelta(seconds=duration)
                ).isoformat(),
            },
        )

    # Start auto timer for new phase
    start_phase_timer(
        db_factory=SessionLocal,
        game_id=game.id,
        room_code=room.code,
        phase=game.phase,
        phase_durations=game_durations,
    )

    # --------------------------------------------------
    # TALLY VOTES (voting → result)
    # --------------------------------------------------

    if request.next_phase == GamePhase.RESULT:
        vote_results = await voting_service.tally_votes(
            db=db,
            game_id=game.id,
            round_number=game.round_number,
        )

        await manager.broadcast_to_room(
            room_code=room.code,
            message={
                "type": "VOTE_RESULTS",
                "results": vote_results.model_dump(),
            },
        )

    # --------------------------------------------------
    # CHECK FINAL-ROUND WIN CONDITION
    # --------------------------------------------------

    if request.next_phase == GamePhase.RESULT:
        win_result = await check_win_condition(
            db=db,
            game_id=game.id,
        )

        if win_result.game_over:
            await calculate_final_scores(
                db=db,
                game_id=game.id,
            )

            game.status = "completed"
            game.phase = GamePhase.GAME_OVER.value

            room.status = "completed"

            await db.commit()

            await db.refresh(game)
            await db.refresh(room)

            game_players = await game_repository.get_game_players(db, game_id=game.id)

            await manager.broadcast_to_room(
                room_code=room.code,
                message={
                    "type": "GAME_OVER",
                    "game": {
                        "id": game.id,
                        "status": game.status,
                        "round_number": game.round_number,
                        "max_rounds": game.max_rounds,
                        "phase": game.phase,
                    },
                    "winner": win_result.winner,
                    "reason": win_result.reason,
                    "scores": [
                        {
                            "user_id": gp.user_id,
                            "role": gp.role,
                            "score": gp.score,
                            "username": (await get_user_by_id(db, gp.user_id)).username,
                        }
                        for gp in game_players
                    ],
                },
            )

            return game

    # --------------------------------------------------
    # TRAIN ML MODEL AFTER GAME OVER
    # --------------------------------------------------

    if request.next_phase == GamePhase.GAME_OVER:
        async def _train_and_broadcast():
            try:
                from app.ml.service import train_model

                async with SessionLocal() as ml_db:
                    ml_result = await train_model(db=ml_db)
                    if ml_result and not ml_result.get("error"):
                        await manager.broadcast_to_room(
                            room_code=room.code,
                            message={
                                "type": "ML_TRAINED",
                                "accuracy": ml_result.get("accuracy"),
                                "samples_used": ml_result.get("samples_used"),
                            },
                        )
            except Exception:
                pass  # ML training is non-critical

        asyncio.create_task(_train_and_broadcast())

    # --------------------------------------------------
    # SEND NEW ROUND MISSIONS TO COORDINATOR
    # --------------------------------------------------

    if request.next_phase == GamePhase.ROUND_START:
        coordinator = await game_repository.get_player_by_role(
            db=db,
            game_id=game.id,
            role="coordinator",
        )

        if coordinator is not None:
            missions = await mission_repository.get_user_missions(
                db=db,
                game_id=game.id,
                user_id=coordinator.user_id,
                round_number=game.round_number,
            )

            await manager.send_to_user(
                room_code=room.code,
                user_id=coordinator.user_id,
                message={
                    "type": "MISSION_ASSIGNMENT",
                    "game_id": game.id,
                    "missions": [
                        {
                            "id": mission.id,
                            "mission_type": (mission.mission_type),
                            "title": mission.title,
                            "description": (mission.description),
                            "target_value": (mission.target_value),
                            "current_value": (mission.current_value),
                            "status": mission.status,
                            "round_number": (mission.round_number),
                        }
                        for mission in missions
                    ],
                },
            )

    return game
