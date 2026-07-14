"""Replay Engine — Pydantic response schemas.

These define the API contract for replay data. The frontend consumes
these shapes to render the replay experience.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Replay Event — the atomic unit of the replay timeline
# ---------------------------------------------------------------------------

class ReplayEvent(BaseModel):
    """A single event in the replay timeline.

    This is a thin wrapper around the GameEvent ORM model,
    shaped for API consumption.
    """

    sequence_number: int
    event_type: str
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    round_number: Optional[int] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime

    # Relative time from game start (seconds)
    relative_time_seconds: float = 0.0

    # Human-readable label for the timeline
    label: str = ""

    # Icon/category for the timeline
    category: str = "other"


# ---------------------------------------------------------------------------
# Replay Player — snapshot of a player's role and identity
# ---------------------------------------------------------------------------

class ReplayPlayer(BaseModel):
    user_id: int
    username: str
    role: str
    score: int = 0


# ---------------------------------------------------------------------------
# Replay Game Info — metadata about the game being replayed
# ---------------------------------------------------------------------------

class ReplayGameInfo(BaseModel):
    game_id: int
    room_code: str
    status: str
    max_rounds: int
    total_events: int
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    players: list[ReplayPlayer] = Field(default_factory=list)
    winner: Optional[str] = None
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Replay Timeline — the full replay data package
# ---------------------------------------------------------------------------

class ReplayTimeline(BaseModel):
    """Complete replay data for a game.

    The frontend loads this once and steps through events client-side.
    """

    game: ReplayGameInfo
    events: list[ReplayEvent] = Field(default_factory=list)
    total_events: int = 0
    total_rounds: int = 0
    duration_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Replay State Snapshot — reconstructed state at a specific event
# ---------------------------------------------------------------------------

class ReplayStateSnapshot(BaseModel):
    """The reconstructed game state at a specific sequence number.

    Used by the debugging use case and future ML pipeline.
    """

    sequence_number: int
    round_number: int
    phase: str
    players: list[ReplayPlayer] = Field(default_factory=list)
    messages_sent: int = 0
    votes_cast: int = 0
    missions_active: int = 0
    missions_completed: int = 0
