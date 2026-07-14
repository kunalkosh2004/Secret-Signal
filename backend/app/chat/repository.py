from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.models import Message
from app.users.models import User


async def create_message(
    db: AsyncSession,
    room_id: int,
    user_id: int,
    content: str,
    reply_to_message_id: int | None = None,
) -> Message:
    message = Message(
        room_id=room_id,
        user_id=user_id,
        content=content,
        reply_to_message_id=reply_to_message_id,
    )

    db.add(message)

    await db.flush()
    await db.refresh(message)

    return message


async def get_room_messages(
    db: AsyncSession,
    room_id: int,
    limit: int = 100,
) -> list[tuple[Message, str]]:
    result = await db.execute(
        select(Message, User.username)
        .join(User, User.id == Message.user_id)
        .where(Message.room_id == room_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(limit)
    )

    return list(reversed(result.all()))


async def get_message_by_id(
    db: AsyncSession,
    message_id: int,
) -> Message | None:
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    return result.scalar_one_or_none()
