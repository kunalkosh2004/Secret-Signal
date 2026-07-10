import random
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.missions import repository as mission_repository


MISSION_TEMPLATES = [
    {
        "mission_type": "send_messages",
        "title": "Stay Active",
        "description": "Send messages during the interaction phase.",
        "target_value": 5,
    },
]

async def generate_missions(
    db: AsyncSession,
    game_id: int,
    coordinator_user_id: int,
    round_number: int,
    mission_count: int = 1,
):
    existing_missions = await mission_repository.get_game_missions(
        db=db,
        game_id=game_id,
        round_number=round_number,
    )

    if existing_missions:
        return existing_missions
    if mission_count > len(MISSION_TEMPLATES):
        raise ValueError(
            "Mission count exceeds available mission templates"
        )

    selected_templates = random.sample(
        MISSION_TEMPLATES,
        k=mission_count,
    )

    missions = []

    try:
        for template in selected_templates:
            mission = await mission_repository.create_mission(
                db=db,
                game_id=game_id,
                assigned_to_user_id=coordinator_user_id,
                mission_type=template["mission_type"],
                title=template["title"],
                description=template["description"],
                target_value=template["target_value"],
                round_number=round_number,
            )

            missions.append(mission)

        await db.flush()

        for mission in missions:
            await db.refresh(mission)

        return missions

    except Exception:
        raise

async def check_mission_completion(
    db: AsyncSession,
    mission_id: int,
) -> bool:
    mission = await mission_repository.get_by_id(
        db=db,
        mission_id=mission_id,
    )

    if mission is None:
        raise ValueError("Mission not found")

    if mission.status == "completed":
        return True

    if mission.current_value < mission.target_value:
        return False

    mission.status = "completed"
    mission.completed_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(mission)

        return True

    except Exception:
        await db.rollback()
        raise

async def get_mission_progress(
    db: AsyncSession,
    game_id: int,
    round_number: int,
):
    missions = await mission_repository.get_game_missions(
        db=db,
        game_id=game_id,
        round_number=round_number,
    )

    return [
        {
            "mission_id": mission.id,
            "current_value": mission.current_value,
            "target_value": mission.target_value,
            "status": mission.status,
        }
        for mission in missions
    ]

async def increment_mission_progress(
    db: AsyncSession,
    game_id: int,
    user_id: int,
    mission_type: str,
    round_number: int,
    increment_by: int = 1,
):
    mission = await mission_repository.get_active_mission_by_type(
        db=db,
        game_id=game_id,
        user_id=user_id,
        mission_type=mission_type,
        round_number=round_number,
    )

    if mission is None:
        return None

    new_value = min(
        mission.current_value + increment_by,
        mission.target_value,
    )

    await mission_repository.update_mission_progress(
        db=db,
        mission=mission,
        current_value=new_value,
    )

    if mission.current_value >= mission.target_value:
        mission.status = "completed"
        mission.completed_at = datetime.now(timezone.utc)

    await db.flush()

    return mission