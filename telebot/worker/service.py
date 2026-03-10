import asyncio
import logging
from typing import Awaitable, Callable

from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from telebot.agents.factory import AgnoFactory
from telebot.common.constants import PROGRESS_STAGES, WORKER_POLL_INTERVAL_SECONDS
from telebot.common.enums import CommandName, JobStatus, SessionStatus
from telebot.common.messages import (
    TEXT_ANALYSIS_EMPTY_RESULT,
    TEXT_ANALYSIS_RATE_LIMITED,
    TEXT_GENERIC_WORKFLOW_FAILURE,
    TEXT_JOB_PROGRESS_TEMPLATE,
    TEXT_WORKER_PING_OK,
)
from telebot.config import Settings
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
        self.twitter_client = TwitterApiClient(settings.twitter_api_key)
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
            if job.command == CommandName.PING_WORKER.value:
                await jobs.mark_running(job, "worker_ping", PROGRESS_STAGES["worker_ping"])
                await jobs.mark_completed(job, TEXT_WORKER_PING_OK)
                await session.commit()
                await self._send_progress(
                    job.telegram_user_id,
                    "worker_ping",
                    TEXT_WORKER_PING_OK,
                )
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
        workflow = build_analysis_workflow(self.session_factory, self.twitter_client, self.agno_factory)
        try:
            await workflow.arun(
                input="Analyze today's content landscape",
                additional_data={
                    "context": AnalysisContext(
                        telegram_user_id=job.telegram_user_id,
                        x_username=user.x_username,
                        x_id=user.x_id or "",
                        progress_callback=progress_notifier,
                    )
                },
            )
            async with self.session_factory() as session:
                jobs = JobRepository(session)
                users = UserRepository(session)
                posts = PostRepository(session)
                job = await jobs.get_job(job_id)
                if job is None:
                    return
                if not await posts.has_analysis_for_today(job.telegram_user_id):
                    await jobs.mark_failed(job, TEXT_ANALYSIS_EMPTY_RESULT)
                    await users.set_status(job.telegram_user_id, SessionStatus.IDLE)
                    await session.commit()
                    await self._send_progress(
                        job.telegram_user_id,
                        JobStatus.FAILED.value,
                        TEXT_ANALYSIS_EMPTY_RESULT,
                    )
                    return
                await jobs.mark_completed(job, PROGRESS_STAGES["complete"])
                await users.set_status(job.telegram_user_id, SessionStatus.IDLE)
                await session.commit()
            await self._send_progress(job.telegram_user_id, "complete", PROGRESS_STAGES["complete"])
        except Exception as exc:
            async with self.session_factory() as session:
                jobs = JobRepository(session)
                users = UserRepository(session)
                job = await jobs.get_job(job_id)
                if job is None:
                    return
                await jobs.mark_failed(job, self._public_error_message(exc))
                await users.set_status(job.telegram_user_id, SessionStatus.IDLE)
                await session.commit()
            await self._send_progress(
                job.telegram_user_id,
                JobStatus.FAILED.value,
                self._public_error_message(exc),
            )

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
