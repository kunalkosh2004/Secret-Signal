from datetime import datetime

from pydantic import BaseModel


class MissionState(BaseModel):
    id: int
    game_id: int
    assigned_to_user_id: int
    mission_type: str
    title: str
    description: str
    target_value: int
    current_value: int
    status: str
    round_number: int
    created_at: datetime
    completed_at: datetime | None

    model_config = {
        "from_attributes": True
    }


class MissionProgress(BaseModel):
    mission_id: int
    current_value: int
    target_value: int
    status: str