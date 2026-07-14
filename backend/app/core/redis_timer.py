"""
Redis-backed game phase timers.

Replaces in-memory asyncio.Task dict with Redis keys + TTL,
making timers durable across server restarts.

Key patterns:
  timer:game:{game_id}           → JSON{phase, room_code, started_at}
  timer:game:{game_id}:deadline  → timestamp (epoch seconds)
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.core.redis import redis_client


PHASE_DURATIONS = {
    "role_assignment": 6,
    "round_start": 5,
    "interaction": 120,
    "discussion": 90,
    "voting": None,
    "result": 10,
}

_active_tasks: dict[int, asyncio.Task] = {}


def get_phase_duration(
    phase: str,
    overrides: dict[str, int] | None = None,
) -> int | None:
    """Return the duration for a phase, using overrides if provided."""
    if overrides and phase in overrides:
        return overrides[phase]
    return PHASE_DURATIONS.get(phase)


def _timer_key(game_id: int) -> str:
    return f"timer:game:{game_id}"


def _deadline_key(game_id: int) -> str:
    return f"timer:game:{game_id}:deadline"


async def store_timer_state(
    game_id: int,
    phase: str,
    room_code: str,
    overrides: dict[str, int] | None = None,
) -> None:
    """Persist timer metadata in Redis."""
    duration = get_phase_duration(phase, overrides)
    if duration is None:
        return

    state = {
        "phase": phase,
        "room_code": room_code,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "duration": duration,
    }
    deadline = datetime.now(timezone.utc) + timedelta(seconds=duration)

    pipe = redis_client.pipeline()
    pipe.set(_timer_key(game_id), json.dumps(state), ex=duration + 30)
    pipe.set(_deadline_key(game_id), str(deadline.timestamp()), ex=duration + 30)
    await pipe.execute()


async def get_timer_state(
    game_id: int,
) -> Optional[dict]:
    """Retrieve timer metadata from Redis."""
    raw = await redis_client.get(_timer_key(game_id))
    if raw is None:
        return None
    return json.loads(raw)


async def get_remaining_time(
    game_id: int,
    phase: str,
    overrides: dict[str, int] | None = None,
) -> float:
    """Return remaining seconds for a game's current phase timer."""
    duration = get_phase_duration(phase, overrides)
    if duration is None:
        return -1

    deadline_raw = await redis_client.get(_deadline_key(game_id))
    if deadline_raw is None:
        return duration

    deadline = float(deadline_raw)
    remaining = max(0, deadline - datetime.now(timezone.utc).timestamp())
    return remaining


async def clear_timer_state(game_id: int) -> None:
    """Remove timer metadata from Redis."""
    pipe = redis_client.pipeline()
    pipe.delete(_timer_key(game_id))
    pipe.delete(_deadline_key(game_id))
    await pipe.execute()


def start_phase_timer(
    game_id: int,
    room_code: str,
    phase: str,
    db_factory,
    broadcast_fn=None,
    phase_durations: dict[str, int] | None = None,
) -> None:
    """
    Start an in-process asyncio timer for the given phase.
    The timer also writes deadline to Redis for reconnect recovery.
    """
    cancel_timer(game_id)

    duration = get_phase_duration(phase, phase_durations)
    if duration is None:
        return

    async def _run():
        try:
            # Store deadline in Redis for reconnect clients
            await store_timer_state(game_id, phase, room_code, phase_durations)

            await asyncio.sleep(duration)

            # Timer expired — advance phase
            from app.game_engine import repository as game_repository
            from app.game_engine.state_machine import GamePhase, VALID_TRANSITIONS
            from app.events import repository as event_repository
            from app.websocket.manager import manager

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

                if current == GamePhase.RESULT and next_phase == GamePhase.ROUND_START:
                    game.round_number += 1

                if next_phase == GamePhase.GAME_OVER:
                    game.status = "completed"

                await db.commit()

                await manager.broadcast_to_room(
                    room_code=room_code,
                    message={
                        "type": "PHASE_CHANGED",
                        "game": {
                            "id": game_id,
                            "phase": next_phase.value,
                            "round_number": game.round_number,
                            "max_rounds": game.max_rounds,
                        },
                    },
                )

                game_durations = game.phase_durations or {}
                next_duration = get_phase_duration(next_phase.value, game_durations)
                if next_duration:
                    deadline = datetime.now(timezone.utc) + timedelta(
                        seconds=next_duration
                    )
                    await manager.broadcast_to_room(
                        room_code=room_code,
                        message={
                            "type": "TIMER_UPDATED",
                            "phase": next_phase.value,
                            "duration_seconds": next_duration,
                            "ends_at": deadline.isoformat(),
                        },
                    )

                # Chain next timer
                start_phase_timer(
                    game_id=game_id,
                    room_code=room_code,
                    phase=next_phase.value,
                    db_factory=db_factory,
                    broadcast_fn=broadcast_fn,
                    phase_durations=game_durations,
                )

        except asyncio.CancelledError:
            await clear_timer_state(game_id)
        except Exception:
            pass

    task = asyncio.create_task(_run())
    _active_tasks[game_id] = task


def cancel_timer(game_id: int) -> None:
    """Cancel an active timer for a game."""
    task = _active_tasks.pop(game_id, None)
    if task and not task.done():
        task.cancel()


def get_active_timer(game_id: int) -> Optional[asyncio.Task]:
    """Return the active timer task for a game, if any."""
    task = _active_tasks.get(game_id)
    if task and not task.done():
        return task
    return None
