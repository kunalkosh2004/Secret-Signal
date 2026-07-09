from datetime import datetime

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
    phase: GamePhase
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class RoleAssignment(BaseModel):
    user_id: int
    role: str