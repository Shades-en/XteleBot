from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from telebot.common.constants import JOB_PREFIX
from telebot.common.enums import JobStatus
from telebot.db.job_models import WorkflowJob


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_job(self, telegram_user_id: int, command: str) -> WorkflowJob:
        job = WorkflowJob(
            job_id=f"{JOB_PREFIX}{uuid4().hex}",
            telegram_user_id=telegram_user_id,
            command=command,
            status=JobStatus.PENDING,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_job(self, job_id: str) -> WorkflowJob | None:
        result = await self.session.execute(
            select(WorkflowJob).where(WorkflowJob.job_id == job_id)
        )
        return result.scalar_one_or_none()

    async def list_pending_jobs(self) -> list[WorkflowJob]:
        result = await self.session.execute(
            select(WorkflowJob)
            .where(WorkflowJob.status == JobStatus.PENDING)
            .order_by(WorkflowJob.created_at.asc())
        )
        return list(result.scalars().all())

    async def latest_for_user(self, telegram_user_id: int) -> WorkflowJob | None:
        result = await self.session.execute(
            select(WorkflowJob)
            .where(WorkflowJob.telegram_user_id == telegram_user_id)
            .order_by(WorkflowJob.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def mark_running(self, job: WorkflowJob, stage: str, message: str) -> None:
        job.status = JobStatus.RUNNING
        job.progress_stage = stage
        job.progress_message = message
        job.started_at = datetime.utcnow()
        await self.session.flush()

    async def mark_progress(self, job: WorkflowJob, stage: str, message: str) -> None:
        job.progress_stage = stage
        job.progress_message = message
        await self.session.flush()

    async def mark_completed(self, job: WorkflowJob, message: str) -> None:
        job.status = JobStatus.COMPLETED
        job.progress_stage = "complete"
        job.progress_message = message
        job.finished_at = datetime.utcnow()
        await self.session.flush()

    async def mark_failed(self, job: WorkflowJob, error_message: str) -> None:
        job.status = JobStatus.FAILED
        job.error_message = error_message
        job.finished_at = datetime.utcnow()
        await self.session.flush()
