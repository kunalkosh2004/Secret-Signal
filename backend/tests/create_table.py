import asyncio

from app.db.base import Base
from app.db.session import engine

# Import the model so it is registered in Base.metadata


async def create_tables():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    print("Tables created successfully")


asyncio.run(create_tables())
