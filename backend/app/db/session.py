from typing import AsyncGenerator
import ssl

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

print(
    "DATABASE_URL =",
    settings.DATABASE_URL.replace(
        settings.DATABASE_URL.split(":")[2].split("@")[0],
        "***",
    ),
)

engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"ssl": ssl.create_default_context()},
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
