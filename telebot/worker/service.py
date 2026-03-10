import asyncio
import logging
from typing import Awaitable, Callable

from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from telebot.agents.factory import AgnoFactory
from telebot.common.constants import PROGRESS_STAGES, WORKER_POLL_INTERVAL_SECONDS
from telebot.common.enums import JobStatus, SessionStatus
from telebot.common.messages import (
    TEXT_ANALYSIS_EMPTY_RESULT,
    TEXT_ANALYSIS_RATE_LIMITED,
    TEXT_GENERIC_WORKFLOW_FAILURE,
    TEXT_JOB_PROGRESS_TEMPLATE,
)
from telebot.config import Settings
from telebot.costs.formatting import format_cost_summary
from telebot.costs.tracker import WorkflowCostTracker
from telebot.db.repositories.jobs import JobRepository
from telebot.db.repositories.posts import PostRepository
from telebot.db.repositories.users import UserRepository
from telebot.telegram.session import create_proxy_session
from telebot.twitter.client import TwitterApiClient
from telebot.workflows.analysis import AnalysisContext, build_analysis_workflow

ProgressNotifier = Callable[[str, str], Awaitable[None]]


class WorkerService:
    def __init__(self, settings: Settings, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self.agno_factory = AgnoFactory(settings)

    async def run_forever(self) -> None:
        while True:
            try:
                await self.process_jobs()
            except Exception:
                logging.exception("Worker cycle failed")
            await asyncio.sleep(WORKER_POLL_INTERVAL_SECONDS)

    async def process_jobs(self) -> None:
        async with self.session_factory() as session:
            jobs = await JobRepository(session).list_pending_jobs()
        for job in jobs:
            await self._process_job(job.job_id)

    async def _process_job(self, job_id: str) -> None:
        async with self.session_factory() as session:
            jobs = JobRepository(session)
            users = UserRepository(session)
            job = await jobs.get_job(job_id)
            if job is None:
                return
            await jobs.mark_running(job, "collecting", PROGRESS_STAGES["collecting"])
            user = await users.ensure_user(job.telegram_user_id)
            if not user.x_username:
                await jobs.mark_failed(job, TEXT_GENERIC_WORKFLOW_FAILURE)
                await session.commit()
                return
            await session.commit()

        progress_notifier = self._build_progress_notifier(job_id, job.telegram_user_id)
        await progress_notifier("collecting", PROGRESS_STAGES["collecting"])
        cost_tracker = WorkflowCostTracker()
        twitter_client = TwitterApiClient(self.settings.twitter_api_key, cost_tracker=cost_tracker)
        workflow = build_analysis_workflow(self.session_factory, twitter_client, self.agno_factory)
        try:
            await workflow.arun(
                input="Analyze today's content landscape",
                additional_data={
                    "context": AnalysisContext(
                        telegram_user_id=job.telegram_user_id,
                        x_username=user.x_username,
                        x_id=user.x_id or "",
                        progress_callback=progress_notifier,
                        cost_tracker=cost_tracker,
                    )
                },
            )
            summary = cost_tracker.summary()
            completion_message = f"{PROGRESS_STAGES['complete']}\n\n{format_cost_summary(summary)}"
            async with self.session_factory() as session:
                jobs = JobRepository(session)
                users = UserRepository(session)
                posts = PostRepository(session)
                job = await jobs.get_job(job_id)
                if job is None:
                    return
                if not await posts.has_analysis_for_today(job.telegram_user_id):
                    failure_summary = cost_tracker.summary()
                    failure_message = (
                        f"{TEXT_ANALYSIS_EMPTY_RESULT}\n\n"
                        f"{format_cost_summary(failure_summary, partial=True)}"
                    )
                    await jobs.apply_cost_summary(job, failure_summary)
                    await jobs.mark_failed(
                        job,
                        TEXT_ANALYSIS_EMPTY_RESULT,
                        progress_message=failure_message,
                    )
                    await users.set_status(job.telegram_user_id, SessionStatus.IDLE)
                    await session.commit()
                    await self._send_progress(
                        job.telegram_user_id,
                        JobStatus.FAILED.value,
                        failure_message,
                    )
                    return
                await jobs.apply_cost_summary(job, summary)
                await jobs.mark_completed(job, completion_message)
                await users.set_status(job.telegram_user_id, SessionStatus.IDLE)
                await session.commit()
            await self._send_progress(job.telegram_user_id, "complete", completion_message)
        except Exception as exc:
            failure_summary = cost_tracker.summary()
            public_error = self._public_error_message(exc)
            failure_message = (
                f"{public_error}\n\n{format_cost_summary(failure_summary, partial=True)}"
            )
            async with self.session_factory() as session:
                jobs = JobRepository(session)
                users = UserRepository(session)
                job = await jobs.get_job(job_id)
                if job is None:
                    return
                await jobs.apply_cost_summary(job, failure_summary)
                await jobs.mark_failed(
                    job,
                    public_error,
                    progress_message=failure_message,
                )
                await users.set_status(job.telegram_user_id, SessionStatus.IDLE)
                await session.commit()
            await self._send_progress(
                job.telegram_user_id,
                JobStatus.FAILED.value,
                failure_message,
            )
        finally:
            await twitter_client.close()

    def _build_progress_notifier(
        self,
        job_id: str,
        telegram_user_id: int,
    ) -> ProgressNotifier:
        async def notify(stage: str, message: str) -> None:
            async with self.session_factory() as session:
                job = await JobRepository(session).get_job(job_id)
                if job is not None:
                    await JobRepository(session).mark_progress(job, stage, message)
                    await session.commit()
            await self._send_progress(telegram_user_id, stage, message)

        return notify

    @staticmethod
    def _public_error_message(exc: Exception) -> str:
        if str(exc) in {TEXT_ANALYSIS_RATE_LIMITED, TEXT_ANALYSIS_EMPTY_RESULT}:
            return str(exc)
        return TEXT_GENERIC_WORKFLOW_FAILURE

    async def _send_progress(self, telegram_user_id: int, stage: str, message: str) -> None:
        if self.settings.bot_env.value == "development":
            bot = Bot(
                token=self.settings.telegram_token,
                session=create_proxy_session(
                    self.settings.proxy_base_url,
                    self.settings.proxy_target,
                    self.settings.vercel_bypass_token,
                ),
            )
        else:
            bot = Bot(token=self.settings.telegram_token)
        try:
            await bot.send_message(
                chat_id=telegram_user_id,
                text=TEXT_JOB_PROGRESS_TEMPLATE.format(stage=stage, message=message),
            )
        finally:
            await bot.session.close()
