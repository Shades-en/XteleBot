from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.common.messages import TEXT_JOB_STATUS_REQUIRED, TEXT_JOB_STATUS_TEMPLATE
from telebot.db.repositories.jobs import JobRepository


class JobStatusWorkflowService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def render_latest_job(self, telegram_user_id: int) -> str:
        async with self.session_factory() as session:
            job = await JobRepository(session).latest_for_user(telegram_user_id)
            if job is None:
                return TEXT_JOB_STATUS_REQUIRED
        return TEXT_JOB_STATUS_TEMPLATE.format(
            job_id=job.job_id,
            command=job.command,
            status=job.status.value,
            stage=job.progress_stage or "not set",
            progress=job.progress_message or "not set",
            error=job.error_message or "none",
        )
