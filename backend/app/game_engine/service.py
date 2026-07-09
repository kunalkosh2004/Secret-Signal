import random
from sqlalchemy.ext.asyncio import AsyncSession

from app.game_engine import repository as game_repository
from app.game_engine.models import Game
from app.rooms import repository as room_repository
from app.game_engine.state_machine import (
    GamePhase,
    validate_transition,
)


def assign_roles(
    user_ids: list[int],
) -> dict[int, str]:
    if len(user_ids) < 3:
        raise ValueError(
            "At least 3 players are required to start a game"
        )

    shuffled_user_ids = user_ids.copy()

    random.shuffle(shuffled_user_ids)

    assignments = {}

    assignments[shuffled_user_ids[0]] = "coordinator"
    assignments[shuffled_user_ids[1]] = "detective"

    for user_id in shuffled_user_ids[2:]:
        assignments[user_id] = "citizen"

    return assignments

async def start_game(
    db: AsyncSession,
    room_code: str,
    requester_id: int,
) -> Game:
    room = await room_repository.get_by_code(
        db,
        room_code,
    )

    if room is None:
        raise ValueError("Room not found")

    if room.host_id != requester_id:
        raise ValueError(
            "Only the room host can start the game"
        )

    if room.status != "waiting":
        raise ValueError(
            "Room is not in waiting state"
        )

    existing_game = await game_repository.get_by_room_id(
        db,
        room_id=room.id,
    )

    if existing_game is not None:
        raise ValueError(
            "A game has already been created for this room"
        )

    players = await room_repository.get_players(
        db,
        room_id=room.id,
    )

    user_ids = [
        player.id
        for player in players
    ]

    role_assignments = assign_roles(user_ids)

    try:
        game = await game_repository.create_game(
            db,
            room_id=room.id,
        )

        for user_id, role in role_assignments.items():
            await game_repository.add_game_player(
                db,
                game_id=game.id,
                user_id=user_id,
                role=role,
            )

        room.status = "in_game"

        await db.commit()
        await db.refresh(game)

        return game

    except Exception:
        await db.rollback()
        raise

async def advance_phase(
    db: AsyncSession,
    game_id: int,
    next_phase: GamePhase,
) -> Game:
    game = await game_repository.get_by_id(
        db,
        game_id=game_id,
    )

    if game is None:
        raise ValueError("Game not found")

    current_phase = GamePhase(game.phase)

    validate_transition(
        current_phase=current_phase,
        next_phase=next_phase,
    )

    game.phase = next_phase.value

    if (
        current_phase == GamePhase.RESULT
        and next_phase == GamePhase.ROUND_START
    ):
        game.round_number += 1

    if next_phase == GamePhase.GAME_OVER:
        game.status = "completed"

    try:
        await db.commit()
        await db.refresh(game)

        return game

    except Exception:
        await db.rollback()
        raise