from typing import AsyncGenerator
import ssl
import os

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from sqlalchemy.engine import make_url

connect_args: dict = {}
db_url = settings.DATABASE_URL or ""
if "localhost" not in db_url and "127.0.0.1" not in db_url:
    connect_args["ssl"] = False

ssl_context = ssl.create_default_context()

DATABASE_URL = (
    os.environ["DATABASE_URL"]
    .replace("postgresql://", "postgresql+asyncpg://", 1)
    .split("?")[0]
)

print("ENGINE URL:", DATABASE_URL)

engine = create_async_engine(
    DATABASE_URL,
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
