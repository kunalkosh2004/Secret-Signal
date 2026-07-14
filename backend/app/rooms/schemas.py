from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class GameSettings(BaseModel):
    max_rounds: int = Field(default=1, ge=1, le=10)
    phase_durations: dict[str, int] = Field(default_factory=dict)

    @field_validator("phase_durations")
    @classmethod
    def validate_phase_durations(cls, v: dict[str, int]) -> dict[str, int]:
        allowed_phases = {
            "role_assignment",
            "round_start",
            "interaction",
            "discussion",
            "result",
        }
        validated = {}
        defaults = {
            "role_assignment": 6,
            "round_start": 5,
            "interaction": 120,
            "discussion": 90,
            "result": 10,
        }
        min_values = {
            "role_assignment": 3,
            "round_start": 3,
            "interaction": 30,
            "discussion": 30,
            "result": 5,
        }
        max_values = {
            "role_assignment": 15,
            "round_start": 15,
            "interaction": 300,
            "discussion": 300,
            "result": 30,
        }
        for phase, duration in v.items():
            if phase not in allowed_phases:
                continue
            if not isinstance(duration, int):
                continue
            clamped = max(min_values[phase], min(duration, max_values[phase]))
            validated[phase] = clamped
        for phase in allowed_phases:
            if phase not in validated:
                validated[phase] = defaults[phase]
        return validated


class CreateRoomRequest(BaseModel):
    max_players: int = Field(default=8, ge=2, le=12)
    settings: dict[str, Any] = Field(default_factory=dict)


class JoinRoomRequest(BaseModel):
    code: str

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()


class RoomResponse(BaseModel):
    id: int
    code: str
    host_id: int
    status: str
    max_players: int
    settings: dict[str, Any]
    created_at: datetime

    model_config = {
        "from_attributes": True
    }