"""
Game phase timer — Redis-backed.

This module now delegates to redis_timer for the actual timer logic.
The original asyncio-based timer is preserved as a fallback.
"""

from datetime import datetime, timezone

from app.core.redis_timer import (
    PHASE_DURATIONS,
    start_phase_timer,
    cancel_timer,
    get_phase_duration,
)

__all__ = [
    "PHASE_DURATIONS",
    "start_phase_timer",
    "cancel_timer",
    "get_remaining_time",
    "get_phase_duration",
]


async def get_remaining_time(phase_started_at: datetime, phase: str) -> float:
    """Calculate remaining time for a phase based on its start time."""
    duration = PHASE_DURATIONS.get(phase)
    if duration is None:
        return -1

    if phase_started_at is None:
        return duration

    elapsed = (datetime.now(timezone.utc) - phase_started_at).total_seconds()
    remaining = max(0, duration - elapsed)
    return remaining
