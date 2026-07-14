from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User


async def get_by_id(
    db: AsyncSession,
    user_id: int,
) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))

    return result.scalar_one_or_none()


async def get_by_email(
    db: AsyncSession,
    email: str,
) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))

    return result.scalar_one_or_none()


async def get_by_username(
    db: AsyncSession,
    username: str,
) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))

    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    **kwargs,
) -> User:
    user = User(**kwargs)

    db.add(user)

    await db.commit()

    await db.refresh(user)

    return user


async def update(
    db: AsyncSession,
    user: User,
    **kwargs,
) -> User:
    for key, value in kwargs.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)

    return user
