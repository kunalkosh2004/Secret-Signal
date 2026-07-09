from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.game_engine.schemas import (
    AdvancePhaseRequest,
    GameState,
)
from app.game_engine.service import (
    advance_phase as advance_phase_service,
    start_game as start_game_service,
)
from app.users.models import User
from app.game_engine import repository as game_repository
from app.rooms import repository as room_repository
from app.websocket.manager import manager


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

        await manager.broadcast_to_room(
            room_code=normalized_room_code,
            message={
                "type": "GAME_START",
                "game": {
                    "id": game.id,
                    "room_id": game.room_id,
                    "status": game.status,
                    "round_number": game.round_number,
                    "phase": game.phase,
                },
            },
        )

        game_players = await game_repository.get_game_players(
            db,
            game_id=game.id,
        )

        for game_player in game_players:
            await manager.send_to_user(
                room_code=normalized_room_code,
                user_id=game_player.user_id,
                message={
                    "type": "ROLE_ASSIGNMENT",
                    "game_id": game.id,
                    "role": game_player.role,
                },
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

    if room.host_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the room host can advance the phase",
        )

    try:
        game = await advance_phase_service(
            db=db,
            game_id=game_id,
            next_phase=request.next_phase,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

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

    return game