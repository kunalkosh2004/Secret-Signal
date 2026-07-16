import asyncio
from logging.config import fileConfig
import ssl

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

from app.core.config import settings
from app.db.base import Base

# Import models so they are registered in Base.metadata
# noqa: F401 — these imports register SQLAlchemy tables for autogenerate
from app.users.models import User  # noqa: F401
from app.auth.models import AuthIdentity  # noqa: F401
from app.rooms.models import Room, RoomPlayer  # noqa: F401
from app.game_engine.models import Game, GamePlayer  # noqa: F401
from app.missions.models import Mission  # noqa: F401
from app.chat.models import Message  # noqa: F401
from app.voting.models import Vote  # noqa: F401
from app.events.models import GameEvent  # noqa: F401

config = context.config

config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL,
)


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    ssl_context = ssl.create_default_context()
    print(repr(settings.DATABASE_URL))
    connectable = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"ssl": ssl_context},
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
