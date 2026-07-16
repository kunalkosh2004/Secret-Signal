from typing import AsyncGenerator
import ssl

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

connect_args: dict = {}
db_url = settings.DATABASE_URL or ""
if "localhost" not in db_url and "127.0.0.1" not in db_url:
    connect_args["ssl"] = False

ssl_context = ssl.create_default_context()

engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"ssl": ssl_context},
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
