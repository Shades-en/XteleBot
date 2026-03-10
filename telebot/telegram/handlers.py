from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.common.commands import COMMAND_PREFIX
from telebot.common.enums import CommandName, SessionStatus
from telebot.common.messages import (
    TEXT_ANALYSIS_ALREADY_EXISTS,
    TEXT_ANALYSIS_QUEUED,
    TEXT_COMMAND_PANEL,
    TEXT_HELP_INTRO,
    TEXT_PONG,
    TEXT_RANDOM_FALLBACK,
    TEXT_REANALYSIS_QUEUED,
    TEXT_SETUP_REQUIRED,
    TEXT_UNRECOGNIZED_COMMAND,
)
from telebot.db.repositories.jobs import JobRepository
from telebot.db.repositories.posts import PostRepository
from telebot.db.repositories.users import UserRepository
from telebot.telegram.menus import build_inline_menu
from telebot.workflows.creator import CreatorWorkflowService
from telebot.workflows.admin import AdminWorkflowService
from telebot.workflows.job_status import JobStatusWorkflowService
from telebot.workflows.onboarding import OnboardingWorkflowService
from telebot.workflows.schedule import ScheduleWorkflowService
from telebot.workflows.user_details import UserDetailsWorkflowService


class TelegramHandlers:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        onboarding_service: OnboardingWorkflowService,
        creator_service: CreatorWorkflowService,
        schedule_service: ScheduleWorkflowService,
        user_details_service: UserDetailsWorkflowService,
        job_status_service: JobStatusWorkflowService,
        admin_service: AdminWorkflowService,
    ) -> None:
        self.session_factory = session_factory
        self.onboarding_service = onboarding_service
        self.creator_service = creator_service
        self.schedule_service = schedule_service
        self.user_details_service = user_details_service
        self.job_status_service = job_status_service
        self.admin_service = admin_service

    async def _answer_help(self, message: Message) -> None:
        await message.answer(TEXT_HELP_INTRO)
        await message.answer(TEXT_COMMAND_PANEL, reply_markup=build_inline_menu())

    @staticmethod
    def _effective_user_id(message: Message, actor_user_id: int | None) -> int:
        if actor_user_id is not None:
            return actor_user_id
        return message.from_user.id

    @staticmethod
    def _effective_display_name(
        message: Message,
        actor_display_name: str | None,
    ) -> str:
        if actor_display_name is not None:
            return actor_display_name
        return message.from_user.full_name

    async def handle_start(self, message: Message) -> None:
        await self.onboarding_service.start(message)

    async def handle_help(self, message: Message) -> None:
        await self._answer_help(message)

    async def handle_ping(self, message: Message) -> None:
        await message.answer(TEXT_PONG)

    async def handle_resetschema(self, message: Message) -> None:
        await message.answer(await self.admin_service.reset_schema())

    async def handle_currentuser(
        self,
        message: Message,
        actor_user_id: int | None = None,
        actor_display_name: str | None = None,
    ) -> None:
        await message.answer(
            await self.user_details_service.render_current_user(
                telegram_user_id=self._effective_user_id(message, actor_user_id),
                telegram_display_name=self._effective_display_name(
                    message,
                    actor_display_name,
                ),
            )
        )

    async def handle_schedule(
        self,
        message: Message,
        actor_user_id: int | None = None,
    ) -> None:
        await message.answer(
            await self.schedule_service.render_schedule(
                self._effective_user_id(message, actor_user_id)
            )
        )

    async def handle_jobstatus(
        self,
        message: Message,
        actor_user_id: int | None = None,
    ) -> None:
        await message.answer(
            await self.job_status_service.render_latest_job(
                self._effective_user_id(message, actor_user_id)
            )
        )

    async def handle_analysetoday(
        self,
        message: Message,
        actor_user_id: int | None = None,
    ) -> None:
        telegram_user_id = self._effective_user_id(message, actor_user_id)
        async with self.session_factory() as session:
            posts = PostRepository(session)
            users = UserRepository(session)
            user = await users.ensure_user(telegram_user_id)
            if not user.x_username or not user.x_id:
                await message.answer(TEXT_SETUP_REQUIRED)
                return
            if await posts.has_analysis_for_today(telegram_user_id):
                await message.answer(TEXT_ANALYSIS_ALREADY_EXISTS)
                return
            await self._queue_analysis_job(session, users, telegram_user_id)
            await session.commit()
        await message.answer(TEXT_ANALYSIS_QUEUED)

    async def handle_reanalysefortoday(
        self,
        message: Message,
        actor_user_id: int | None = None,
    ) -> None:
        telegram_user_id = self._effective_user_id(message, actor_user_id)
        async with self.session_factory() as session:
            posts = PostRepository(session)
            users = UserRepository(session)
            user = await users.ensure_user(telegram_user_id)
            if not user.x_username or not user.x_id:
                await message.answer(TEXT_SETUP_REQUIRED)
                return
            await posts.delete_posts_for_today_by_user(telegram_user_id)
            await self._queue_analysis_job(session, users, telegram_user_id)
            await session.commit()
        await message.answer(TEXT_REANALYSIS_QUEUED)

    async def handle_quote(
        self,
        message: Message,
        actor_user_id: int | None = None,
    ) -> None:
        await self.creator_service.handle_command(message, CommandName.QUOTE, actor_user_id=actor_user_id)

    async def handle_comment(
        self,
        message: Message,
        actor_user_id: int | None = None,
    ) -> None:
        await self.creator_service.handle_command(message, CommandName.COMMENT, actor_user_id=actor_user_id)

    async def handle_postbyinspiration(
        self,
        message: Message,
        actor_user_id: int | None = None,
    ) -> None:
        await self.creator_service.handle_command(
            message, CommandName.POST_BY_INSPIRATION, actor_user_id=actor_user_id
        )

    async def handle_creator_alternatives(
        self,
        message: Message,
        actor_user_id: int | None = None,
    ) -> None:
        await self.creator_service.handle_show_alternatives(message, actor_user_id=actor_user_id)

    async def handle_creator_pick(
        self,
        message: Message,
        selected_post_id: str,
        actor_user_id: int | None = None,
    ) -> None:
        await self.creator_service.handle_select_source_post(
            message, selected_post_id, actor_user_id=actor_user_id
        )

    async def handle_text(self, message: Message) -> None:
        if message.text is None:
            return
        if message.text.startswith(COMMAND_PREFIX):
            await message.answer(TEXT_UNRECOGNIZED_COMMAND)
            return
        if await self.onboarding_service.handle_username_reply(message):
            return
        if await self.creator_service.handle_follow_up(message):
            return
        await message.answer(TEXT_RANDOM_FALLBACK)

    @staticmethod
    async def _queue_analysis_job(
        session: AsyncSession,
        users: UserRepository,
        telegram_user_id: int,
    ) -> None:
        jobs = JobRepository(session)
        await users.set_status(
            telegram_user_id,
            SessionStatus.ANALYSIS_RUNNING,
            CommandName.ANALYZE_TODAY.value,
        )
        await jobs.create_job(telegram_user_id, CommandName.ANALYZE_TODAY.value)
