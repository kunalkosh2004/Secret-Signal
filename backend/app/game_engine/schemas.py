from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.game_engine.state_machine import GamePhase


class AdvancePhaseRequest(BaseModel):
    next_phase: GamePhase


class RoundState(BaseModel):
    round_number: int
    phase: GamePhase


class GameState(BaseModel):
    id: int
    room_id: int
    status: str
    round_number: int
    max_rounds: int = 1
    phase: GamePhase
    phase_durations: dict[str, Any] = {}
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleAssignment(BaseModel):
    user_id: int
    role: str


class WinConditionResult(BaseModel):
    game_over: bool
    winner: str | None = None
    reason: str | None = None
