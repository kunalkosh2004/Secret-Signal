import random
from sqlalchemy.ext.asyncio import AsyncSession

from app.game_engine import repository as game_repository
from app.game_engine.models import Game
from app.game_engine.schemas import WinConditionResult
from app.missions.service import generate_missions
from app.rooms import repository as room_repository
from app.missions import repository as mission_repository
from app.events import repository as event_repository
from app.voting import repository as vote_repository
from app.game_engine.state_machine import (
    GamePhase,
    validate_transition,
)

DEFAULT_PHASE_DURATIONS = {
    "role_assignment": 6,
    "round_start": 5,
    "interaction": 120,
    "discussion": 90,
    "result": 10,
}

DEFAULT_MAX_ROUNDS = 1

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

    # All non-host players must be ready
    players_with_ready = await room_repository.get_players_with_ready_state(
        db,
        room_id=room.id,
    )
    for player, is_ready in players_with_ready:
        if player.id != room.host_id and not is_ready:
            raise ValueError(
                "All players must be ready before starting the game"
            )

    user_ids = [
        player.id
        for player in players
    ]

    role_assignments = assign_roles(user_ids)

    try:
        room_settings = room.settings or {}
        game_settings = {
            "max_rounds": room_settings.get("max_rounds", DEFAULT_MAX_ROUNDS),
            "phase_durations": room_settings.get("phase_durations", DEFAULT_PHASE_DURATIONS),
        }

        game = await game_repository.create_game(
            db,
            room_id=room.id,
            max_rounds=game_settings["max_rounds"],
            phase_durations=game_settings["phase_durations"],
        )

        for user_id, role in role_assignments.items():
            await game_repository.add_game_player(
                db,
                game_id=game.id,
                user_id=user_id,
                role=role,
            )
        
        coordinator_user_id = next(
            user_id
            for user_id, role in role_assignments.items()
            if role == "coordinator"
        )

        await generate_missions(
            db=db,
            game_id=game.id,
            coordinator_user_id=coordinator_user_id,
            round_number=game.round_number,
        )

        await event_repository.create_event(
            db=db,
            game_id=game.id,
            round_number=game.round_number,
            event_type="game_started",
            user_id=requester_id,
            payload={
                "room_code": room.code,
                "player_count": len(user_ids),
                "roles": {
                    str(user_id): role
                    for user_id, role in role_assignments.items()
                },
            },
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
    
    if game.status == "completed":
        raise ValueError(
            "Game has already ended"
        )

    current_phase = GamePhase(game.phase)

    validate_transition(
        current_phase=current_phase,
        next_phase=next_phase,
    )

    if (
        current_phase == GamePhase.RESULT
        and next_phase == GamePhase.ROUND_START
        and game.round_number >= game.max_rounds
    ):
        raise ValueError(
            "Maximum rounds reached; game must transition to game_over"
        )

    game.phase = next_phase.value

    await event_repository.create_event(
        db=db,
        game_id=game.id,
        round_number=game.round_number,
        event_type="phase_changed",
        payload={
            "from_phase": current_phase.value,
            "to_phase": next_phase.value,
        },
    )

    if (
        current_phase == GamePhase.RESULT
        and next_phase == GamePhase.ROUND_START
    ):
        game.round_number += 1

        coordinator = await game_repository.get_player_by_role(
            db=db,
            game_id=game.id,
            role="coordinator",
        )

        if coordinator is None:
            raise ValueError(
                "Coordinator not found for game"
            )

        await generate_missions(
            db=db,
            game_id=game.id,
            coordinator_user_id=coordinator.user_id,
            round_number=game.round_number,
        )

    if next_phase == GamePhase.GAME_OVER:
        game.status = "completed"

    try:
        await db.commit()
        await db.refresh(game)

        return game

    except Exception:
        await db.rollback()
        raise

async def check_win_condition(
    db: AsyncSession,
    game_id: int,
) -> WinConditionResult:
    game = await game_repository.get_by_id(
        db,
        game_id=game_id,
    )

    if game is None:
        raise ValueError("Game not found")

    completed_missions = (
        await mission_repository.count_completed_missions(
            db=db,
            game_id=game_id,
        )
    )

    if completed_missions >= game.max_rounds:
        return WinConditionResult(
            game_over=True,
            winner="coordinator",
            reason="mission_target_reached",
        )

    if game.phase == GamePhase.RESULT.value:
        votes = await vote_repository.get_votes_for_round(
            db=db,
            game_id=game_id,
            round_number=game.round_number,
        )
        if votes:
            vote_counts: dict[int, int] = {}
            for v in votes:
                vote_counts[v.target_user_id] = (
                    vote_counts.get(v.target_user_id, 0) + 1
                )
            top_target = max(vote_counts, key=vote_counts.get)
            coordinator = await game_repository.get_player_by_role(
                db=db,
                game_id=game_id,
                role="coordinator",
            )
            if coordinator and top_target == coordinator.user_id:
                return WinConditionResult(
                    game_over=True,
                    winner="investigation_team",
                    reason="coordinator_correctly_identified",
                )

    if (
        game.round_number >= game.max_rounds
        and game.phase == GamePhase.RESULT.value
    ):
        return WinConditionResult(
            game_over=True,
            winner="investigation_team",
            reason="coordinator_failed_mission_target",
        )

    return WinConditionResult(
        game_over=False,
        winner=None,
        reason=None,
    )


async def calculate_final_scores(
    db: AsyncSession,
    game_id: int,
) -> dict[int, int]:
    game = await game_repository.get_by_id(
        db, game_id=game_id
    )

    if game is None:
        raise ValueError("Game not found")

    game_players = await game_repository.get_game_players(
        db, game_id=game_id
    )

    coordinator = next(
        (gp for gp in game_players if gp.role == "coordinator"),
        None,
    )

    if coordinator is None:
        return {gp.user_id: 0 for gp in game_players}

    completed_missions = (
        await mission_repository.count_completed_missions(
            db=db, game_id=game_id
        )
    )

    mission_score = completed_missions * 10

    incorrect_accusations = 0
    for r in range(1, game.round_number + 1):
        votes = await vote_repository.get_votes_for_round(
            db=db, game_id=game_id, round_number=r
        )
        if not votes:
            continue

        vote_counts: dict[int, int] = {}
        for vote in votes:
            vote_counts[vote.target_user_id] = (
                vote_counts.get(vote.target_user_id, 0) + 1
            )

        if not vote_counts:
            continue

        top_target = max(vote_counts, key=vote_counts.get)
        if top_target != coordinator.user_id:
            incorrect_accusations += 1

    correct_accusations = 0
    for r in range(1, game.round_number + 1):
        votes = await vote_repository.get_votes_for_round(
            db=db, game_id=game_id, round_number=r
        )
        if not votes:
            continue

        vote_counts: dict[int, int] = {}
        for vote in votes:
            vote_counts[vote.target_user_id] = (
                vote_counts.get(vote.target_user_id, 0) + 1
            )

        if not vote_counts:
            continue

        top_target = max(vote_counts, key=vote_counts.get)
        if top_target == coordinator.user_id:
            correct_accusations += 1

    scores: dict[int, int] = {}

    coordinator_score = (
        mission_score + incorrect_accusations * 5
    )
    scores[coordinator.user_id] = coordinator_score

    for gp in game_players:
        if gp.role == "coordinator":
            continue
        scores[gp.user_id] = correct_accusations * 10

    for gp in game_players:
        gp.score = scores.get(gp.user_id, 0)

    await db.flush()

    return scores
