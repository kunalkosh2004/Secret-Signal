from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from typing import Optional

from app.missions.models import Mission


async def create_mission(
    db: AsyncSession,
    game_id: int,
    assigned_to_user_id: int,
    mission_type: str,
    title: str,
    description: str,
    target_value: int,
    round_number: int,
) -> Mission:
    mission = Mission(
        game_id=game_id,
        assigned_to_user_id=assigned_to_user_id,
        mission_type=mission_type,
        title=title,
        description=description,
        target_value=target_value,
        current_value=0,
        status="active",
        round_number=round_number,
    )

    db.add(mission)

    await db.flush()

    return mission

async def get_game_missions(
    db: AsyncSession,
    game_id: int,
    round_number: int,
) -> list[Mission]:
    result = await db.execute(
        select(Mission)
        .where(
            Mission.game_id == game_id,
            Mission.round_number == round_number,
        )
        .order_by(Mission.id.asc())
    )

    return list(result.scalars().all())


async def get_by_id(
    db: AsyncSession,
    mission_id: int,
) -> Optional[Mission]:
    result = await db.execute(
        select(Mission).where(
            Mission.id == mission_id
        )
    )

    return result.scalar_one_or_none()

async def update_mission_progress(
    db: AsyncSession,
    mission: Mission,
    current_value: int,
) -> Mission:
    mission.current_value = current_value

    await db.flush()

    return mission

async def get_user_missions(
    db: AsyncSession,
    game_id: int,
    user_id: int,
    round_number: int,
) -> list[Mission]:
    result = await db.execute(
        select(Mission)
        .where(
            Mission.game_id == game_id,
            Mission.assigned_to_user_id == user_id,
            Mission.round_number == round_number,
        )
        .order_by(Mission.id.asc())
    )

    return list(result.scalars().all())

async def get_active_mission_by_type(
    db: AsyncSession,
    game_id: int,
    user_id: int,
    mission_type: str,
    round_number: int,
) -> Optional[Mission]:
    result = await db.execute(
        select(Mission).where(
            Mission.game_id == game_id,
            Mission.assigned_to_user_id == user_id,
            Mission.mission_type == mission_type,
            Mission.round_number == round_number,
            Mission.status == "active",
        )
    )

    return result.scalar_one_or_none()


async def get_active_user_missions(
    db: AsyncSession,
    game_id: int,
    user_id: int,
    round_number: int,
) -> list[Mission]:
    result = await db.execute(
        select(Mission)
        .where(
            Mission.game_id == game_id,
            Mission.assigned_to_user_id == user_id,
            Mission.round_number == round_number,
            Mission.status == "active",
        )
        .order_by(Mission.id.asc())
    )

    return list(result.scalars().all())


async def count_completed_missions(
    db: AsyncSession,
    game_id: int,
) -> int:
    result = await db.execute(
        select(func.count(Mission.id)).where(
            Mission.game_id == game_id,
            Mission.status == "completed",
        )
    )

    return result.scalar_one()
