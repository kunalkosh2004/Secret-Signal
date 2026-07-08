"""
Database session management.

TODO: Implement SQLAlchemy async engine and session factory.

Steps (you implement these):
  1. Create an async engine using `create_async_engine` from SQLAlchemy.
     The connection URL should come from settings (see core/config.py).
     Example for asyncpg:  postgresql+asyncpg://user:pass@localhost:5432/db

  2. Create an async session factory with `async_sessionmaker`.

  3. Create a `get_db` async generator dependency for FastAPI:
       async def get_db() -> AsyncGenerator[AsyncSession, None]:
           async with session_factory() as session:
               yield session

  4. Add the `get_db` dependency to your routers so handler functions
     receive a database session for every request.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session