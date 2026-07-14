from sqlalchemy import select, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.reaction_models import MessageReaction


async def add_reaction(
    db: AsyncSession,
    message_id: int,
    user_id: int,
    emoji: str,
) -> MessageReaction:
    """Add a reaction to a message. Returns existing if already reacted with same emoji."""
    existing = await get_reaction(db, message_id, user_id, emoji)
    if existing:
        return existing

    reaction = MessageReaction(
        message_id=message_id,
        user_id=user_id,
        emoji=emoji,
    )
    db.add(reaction)
    await db.flush()
    await db.refresh(reaction)
    return reaction


async def remove_reaction(
    db: AsyncSession,
    message_id: int,
    user_id: int,
    emoji: str,
) -> bool:
    """Remove a reaction. Returns True if removed, False if not found."""
    reaction = await get_reaction(db, message_id, user_id, emoji)
    if reaction is None:
        return False

    await db.delete(reaction)
    await db.flush()
    return True


async def get_reaction(
    db: AsyncSession,
    message_id: int,
    user_id: int,
    emoji: str,
) -> MessageReaction | None:
    """Get a specific reaction."""
    result = await db.execute(
        select(MessageReaction).where(
            MessageReaction.message_id == message_id,
            MessageReaction.user_id == user_id,
            MessageReaction.emoji == emoji,
        )
    )
    return result.scalar_one_or_none()


async def get_reactions_for_message(
    db: AsyncSession,
    message_id: int,
) -> list[MessageReaction]:
    """Get all reactions for a message."""
    result = await db.execute(
        select(MessageReaction)
        .where(MessageReaction.message_id == message_id)
        .order_by(MessageReaction.created_at)
    )
    return list(result.scalars().all())


async def get_reactions_for_messages(
    db: AsyncSession,
    message_ids: list[int],
) -> list[MessageReaction]:
    """Get all reactions for a list of messages."""
    if not message_ids:
        return []

    result = await db.execute(
        select(MessageReaction)
        .where(MessageReaction.message_id.in_(message_ids))
        .order_by(MessageReaction.created_at)
    )
    return list(result.scalars().all())


async def get_reaction_counts(
    db: AsyncSession,
    message_id: int,
) -> dict[str, list[int]]:
    """
    Get reaction counts grouped by emoji for a message.
    Returns {emoji: [user_id, ...]}
    """
    result = await db.execute(
        select(MessageReaction.emoji, MessageReaction.user_id)
        .where(MessageReaction.message_id == message_id)
        .order_by(MessageReaction.emoji, MessageReaction.user_id)
    )

    counts: dict[str, list[int]] = {}
    for emoji, user_id in result.all():
        if emoji not in counts:
            counts[emoji] = []
        counts[emoji].append(user_id)

    return counts
