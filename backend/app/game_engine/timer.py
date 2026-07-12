import asyncio
from datetime import datetime, timezone, timedelta

from app.game_engine import repository as game_repository
from app.game_engine.state_machine import GamePhase, VALID_TRANSITIONS
from app.websocket.manager import manager

PHASE_DURATIONS = {
    GamePhase.ROLE_ASSIGNMENT.value: 6,
    GamePhase.ROUND_START.value: 5,
    GamePhase.INTERACTION.value: 120,
    GamePhase.DISCUSSION.value: 90,
    GamePhase.VOTING.value: None,
    GamePhase.RESULT.value: 10,
}

_active_timers: dict[int, asyncio.Task] = {}


async def start_phase_timer(
    db_factory,
    game_id: int,
    room_code: str,
    phase: str,
    broadcast_fn=None,
):
    cancel_timer(game_id)

    duration = PHASE_DURATIONS.get(phase)

    if duration is None:
        return

    async def _timer():
        try:
            await asyncio.sleep(duration)

            async with db_factory() as db:
                game = await game_repository.get_by_id(db, game_id)

                if game is None or game.status == "completed":
                    return

                if game.phase != phase:
                    return

                current = GamePhase(game.phase)
                transitions = VALID_TRANSITIONS.get(current, set())

                if not transitions:
                    return

                next_phase = next(iter(transitions))

                game.phase = next_phase.value
                game.phase_started_at = datetime.now(timezone.utc)

                from app.events import repository as event_repository

                await event_repository.create_event(
                    db=db,
                    game_id=game_id,
                    event_type="phase_changed",
                    payload={
                        "from_phase": current.value,
                        "to_phase": next_phase.value,
                        "auto": True,
                    },
                    round_number=game.round_number,
                )

                if (
                    current == GamePhase.RESULT
                    and next_phase == GamePhase.ROUND_START
                ):
                    game.round_number += 1

                if next_phase == GamePhase.GAME_OVER:
                    game.status = "completed"

                await db.commit()

                if broadcast_fn:
                    await broadcast_fn(
                        room_code=room_code,
                        game_id=game_id,
                        new_phase=next_phase.value,
                        round_number=game.round_number,
                    )
                else:
                    await manager.broadcast_to_room(
                        room_code=room_code,
                        message={
                            "type": "PHASE_CHANGED",
                            "game": {
                                "id": game_id,
                                "phase": next_phase.value,
                                "round_number": game.round_number,
                            },
                        },
                    )

                    next_duration = PHASE_DURATIONS.get(next_phase.value)
                    if next_duration:
                        await manager.broadcast_to_room(
                            room_code=room_code,
                            message={
                                "type": "TIMER_UPDATED",
                                "phase": next_phase.value,
                                "duration_seconds": next_duration,
                                "ends_at": (
                                    datetime.now(timezone.utc)
                                    + timedelta(seconds=next_duration)
                                ).isoformat(),
                            },
                        )

                await start_phase_timer(
                    db_factory=db_factory,
                    game_id=game_id,
                    room_code=room_code,
                    phase=next_phase.value,
                    broadcast_fn=broadcast_fn,
                )

        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    task = asyncio.create_task(_timer())
    _active_timers[game_id] = task


def cancel_timer(game_id: int):
    task = _active_timers.pop(game_id, None)
    if task and not task.done():
        task.cancel()


def get_remaining_time(phase_started_at: datetime, phase: str) -> float:
    duration = PHASE_DURATIONS.get(phase)
    if duration is None:
        return -1

    if phase_started_at is None:
        return duration

    elapsed = (datetime.now(timezone.utc) - phase_started_at).total_seconds()
    remaining = max(0, duration - elapsed)
    return remaining
