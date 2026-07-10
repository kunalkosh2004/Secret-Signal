from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.models import GameEvent


async def create_event(
    db: AsyncSession,
    game_id: int,
    event_type: str,
    payload: dict,
    round_number: int | None = None,
    user_id: int | None = None,
) -> GameEvent:
    event = GameEvent(
        game_id=game_id,
        round_number=round_number,
        event_type=event_type,
        user_id=user_id,
        payload=payload,
    )

    db.add(event)
    await db.flush()

    return event


async def get_game_events(
    db: AsyncSession,
    game_id: int,
) -> list[GameEvent]:
    result = await db.execute(
        select(GameEvent)
        .where(GameEvent.game_id == game_id)
        .order_by(GameEvent.created_at.asc(), GameEvent.id.asc())
    )

    return list(result.scalars().all())
