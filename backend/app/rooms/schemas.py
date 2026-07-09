from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


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