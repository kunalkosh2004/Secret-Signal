from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.training.models import TrainingMessage


async def create_training_message(
    db: AsyncSession,
    game_id: int,
    user_id: int,
    role: str,
    phase: str,
    content: str,
    round_number: int,
) -> TrainingMessage:
    message = TrainingMessage(
        game_id=game_id,
        user_id=user_id,
        role=role,
        phase=phase,
        content=content,
        round_number=round_number,
    )

    db.add(message)
    await db.flush()

    return message


async def get_game_training_data(
    db: AsyncSession,
    game_id: int,
) -> list[TrainingMessage]:
    result = await db.execute(
        select(TrainingMessage)
        .where(TrainingMessage.game_id == game_id)
        .order_by(TrainingMessage.created_at.asc(), TrainingMessage.id.asc())
    )

    return list(result.scalars().all())


async def get_all_training_data(
    db: AsyncSession,
) -> list[TrainingMessage]:
    result = await db.execute(
        select(TrainingMessage)
        .order_by(TrainingMessage.created_at.asc(), TrainingMessage.id.asc())
    )

    return list(result.scalars().all())


async def get_training_data_count(
    db: AsyncSession,
) -> int:
    result = await db.execute(
        select(func.count(TrainingMessage.id))
    )

    return result.scalar_one()
