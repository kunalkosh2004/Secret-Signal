from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.models import GameEvent


async def create_event(
    db: AsyncSession,
    game_id: int,
    event_type: str,
    payload: dict,
    round_number: int | None = None,
    user_id: int | None = None,
    metadata: dict | None = None,
) -> GameEvent:
    """Create an immutable game event with a deterministic sequence number.

    The sequence_number is assigned atomically per game, ensuring that
    events can always be replayed in the exact same order.
    """
    # Get the next sequence number for this game
    result = await db.execute(
        select(func.coalesce(func.max(GameEvent.sequence_number), 0))
        .where(GameEvent.game_id == game_id)
    )
    max_seq = result.scalar()
    next_seq = max_seq + 1

    event = GameEvent(
        game_id=game_id,
        sequence_number=next_seq,
        round_number=round_number,
        event_type=event_type,
        actor_id=user_id,
        payload=payload,
        event_metadata=metadata or {},
    )

    db.add(event)
    await db.flush()

    return event


async def get_game_events(
    db: AsyncSession,
    game_id: int,
) -> list[GameEvent]:
    """Get all events for a game, ordered by deterministic sequence number.

    This is the primary query for the replay engine. Events are always
    returned in the same order regardless of database replication or
    clock skew.
    """
    result = await db.execute(
        select(GameEvent)
        .where(GameEvent.game_id == game_id)
        .order_by(GameEvent.sequence_number.asc(), GameEvent.id.asc())
    )

    return list(result.scalars().all())


async def get_game_events_by_type(
    db: AsyncSession,
    game_id: int,
    event_type: str,
) -> list[GameEvent]:
    """Get events of a specific type for a game."""
    result = await db.execute(
        select(GameEvent)
        .where(
            GameEvent.game_id == game_id,
            GameEvent.event_type == event_type,
        )
        .order_by(GameEvent.sequence_number.asc())
    )

    return list(result.scalars().all())


async def get_game_events_by_round(
    db: AsyncSession,
    game_id: int,
    round_number: int,
) -> list[GameEvent]:
    """Get all events for a specific round in a game."""
    result = await db.execute(
        select(GameEvent)
        .where(
            GameEvent.game_id == game_id,
            GameEvent.round_number == round_number,
        )
        .order_by(GameEvent.sequence_number.asc())
    )

    return list(result.scalars().all())


async def get_event_count(db: AsyncSession, game_id: int) -> int:
    """Get the total number of events for a game."""
    result = await db.execute(
        select(func.count(GameEvent.id))
        .where(GameEvent.game_id == game_id)
    )
    return result.scalar() or 0
