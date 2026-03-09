from sqlalchemy.ext.asyncio import AsyncEngine

from telebot.db.base import Base
from telebot.db import schema  # noqa: F401


async def create_schema(engine: AsyncEngine, reset_schema: bool = False) -> None:
    async with engine.begin() as connection:
        if reset_schema:
            await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


async def reset_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
