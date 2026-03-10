from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.common.enums import CommandName
from telebot.common.messages import TEXT_CREATOR_JOB_COMPLETED
from telebot.costs.schemas import WorkflowCostSummary
from telebot.db.repositories.jobs import JobRepository


async def start_creator_job(
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user_id: int,
    command: CommandName,
    progress_message: str,
) -> str:
    async with session_factory() as session:
        jobs = JobRepository(session)
        job = await jobs.create_job(telegram_user_id, command.value)
        await jobs.mark_running(job, "drafting", progress_message)
        await session.commit()
        return job.job_id


async def complete_creator_job(
    session_factory: async_sessionmaker[AsyncSession],
    job_id: str,
    summary: WorkflowCostSummary,
) -> None:
    async with session_factory() as session:
        jobs = JobRepository(session)
        job = await jobs.get_job(job_id)
        if job is None:
            return
        await jobs.apply_cost_summary(job, summary)
        await jobs.mark_completed(job, TEXT_CREATOR_JOB_COMPLETED)
        await session.commit()


async def fail_creator_job(
    session_factory: async_sessionmaker[AsyncSession],
    job_id: str,
    error_message: str,
    summary: WorkflowCostSummary,
) -> None:
    async with session_factory() as session:
        jobs = JobRepository(session)
        job = await jobs.get_job(job_id)
        if job is None:
            return
        await jobs.apply_cost_summary(job, summary)
        await jobs.mark_failed(job, error_message)
        await session.commit()
