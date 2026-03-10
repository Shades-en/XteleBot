from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from telebot.db.base import Base
from telebot.db import schema  # noqa: F401


async def create_schema(engine: AsyncEngine, reset_schema: bool = False) -> None:
    async with engine.begin() as connection:
        if reset_schema:
            await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
        await _ensure_workflow_job_cost_columns(connection)
        await _ensure_app_session_creator_state_column(connection)


async def reset_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


async def _ensure_workflow_job_cost_columns(connection) -> None:
    await connection.execute(
        text(
            "ALTER TABLE workflow_jobs "
            "ADD COLUMN IF NOT EXISTS total_cost_usd NUMERIC(12, 6)"
        )
    )
    await connection.execute(
        text(
            "ALTER TABLE workflow_jobs "
            "ADD COLUMN IF NOT EXISTS cost_breakdown JSON"
        )
    )


async def _ensure_app_session_creator_state_column(connection) -> None:
    await connection.execute(
        text(
            "ALTER TABLE app_sessions "
            "ADD COLUMN IF NOT EXISTS creator_state JSON"
        )
    )
