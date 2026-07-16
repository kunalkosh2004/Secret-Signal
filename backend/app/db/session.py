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
import reprlib

print("=" * 80)
print("DB URL repr:", repr(settings.DATABASE_URL))
print("DB URL len :", len(settings.DATABASE_URL))
print("=" * 80)

# ---------- DEBUG ----------
u = make_url(settings.DATABASE_URL)

print("=" * 80)
print("Host:", u.host)
print("User:", u.username)
print("Database:", u.database)
print("Password length:", len(u.password or ""))
print("Password starts with:", (u.password or "")[:5])
print("=" * 80)
# ---------------------------

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
