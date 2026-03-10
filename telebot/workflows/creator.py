import asyncio

from agno.media import Image
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.agents.factory import AgnoFactory
from telebot.common.constants import ALLOWED_URL_PREFIXES, CREATOR_SOURCE_MEDIA_LIMIT
from telebot.common.enums import CommandName, PostPurpose, SessionStatus
from telebot.common.messages import (
    TEXT_ANALYSIS_REQUIRED,
    TEXT_CREATOR_SOURCE_REQUIRED,
    TEXT_SETUP_REQUIRED,
    TEXT_SOURCE_POST_LINK_TEMPLATE,
)
from telebot.db.repositories.posts import PostRepository
from telebot.db.repositories.users import UserRepository
from telebot.workflows.creator_prompting import build_creator_prompt
from telebot.workflows.creator_types import (
    CreatorContext,
    CreatorSourcePost,
    CreatorStyleExample,
)


class CreatorWorkflowService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        agno_factory: AgnoFactory,
    ) -> None:
        self.session_factory = session_factory
        self.agno_factory = agno_factory

    async def handle_command(
        self,
        message: Message,
        command: CommandName,
        actor_user_id: int | None = None,
    ) -> None:
        telegram_user_id = actor_user_id if actor_user_id is not None else message.from_user.id
        async with self.session_factory() as session:
            users = UserRepository(session)
            user = await users.ensure_user(telegram_user_id)
            if not user.x_username or not user.x_id:
                await message.answer(TEXT_SETUP_REQUIRED)
                return
            context = await self._creator_context(telegram_user_id, command)
            if context is None:
                await message.answer(self._unavailable_message(command))
                return
            await users.set_status(
                telegram_user_id,
                self._status_for_command(command),
                command.value,
            )
            await session.commit()
            draft = await self._generate_draft(
                session_id=user.current_session_id or "",
                telegram_user_id=telegram_user_id,
                context=context,
            )
        await message.answer(draft)

    async def handle_follow_up(self, message: Message) -> bool:
        async with self.session_factory() as session:
            users = UserRepository(session)
            current_session = await users.get_current_session(message.from_user.id)
            user = await users.ensure_user(message.from_user.id)
            if current_session is None or current_session.status not in {
                SessionStatus.GENERATING_POST,
                SessionStatus.GENERATING_QUOTE,
                SessionStatus.GENERATING_COMMENT,
            }:
                return False
            command = self._command_from_session(current_session)
            if command is None:
                return False
            context = await self._creator_context(
                message.from_user.id,
                command,
                refinement=message.text,
            )
            if context is None:
                await message.answer(self._unavailable_message(command))
                return True
            draft = await self._generate_draft(
                session_id=user.current_session_id or current_session.session_id,
                telegram_user_id=message.from_user.id,
                context=context,
            )
        await message.answer(draft)
        return True

    async def _creator_context(
        self,
        telegram_user_id: int,
        command: CommandName,
        refinement: str | None = None,
    ) -> CreatorContext | None:
        source_post, style_examples = await asyncio.gather(
            self._load_creator_source_post(
                telegram_user_id,
                self._purpose_for_command(command),
            ),
            self._load_creator_style_examples(telegram_user_id),
        )
        if source_post is None:
            return None
        return CreatorContext(
            command=command,
            source_post=self._creator_source_post(source_post),
            style_examples=[
                CreatorStyleExample(
                    post_id=post.post_id,
                    text=post.text or "",
                    posted_at=post.posted_at.isoformat() if post.posted_at else None,
                )
                for post in style_examples
            ],
            refinement=refinement,
        )

    async def _load_creator_source_post(
        self,
        telegram_user_id: int,
        purpose: PostPurpose,
    ):
        async with self.session_factory() as session:
            return await PostRepository(session).best_researched_post_for_creator(
                telegram_user_id,
                purpose,
            )

    async def _load_creator_style_examples(self, telegram_user_id: int):
        async with self.session_factory() as session:
            return await PostRepository(session).recent_own_posts_for_creator_style(
                telegram_user_id
            )

    async def _generate_draft(
        self,
        session_id: str,
        telegram_user_id: int,
        context: CreatorContext,
    ) -> str:
        response = await self.agno_factory.build_creator_agent().arun(
            build_creator_prompt(context),
            user_id=str(telegram_user_id),
            session_id=session_id,
            images=self._creator_images(context),
        )
        draft = str(response.content)
        source_url = context.source_post.source_url
        if source_url is None:
            return draft
        return f"{draft}{TEXT_SOURCE_POST_LINK_TEMPLATE.format(source_url=source_url)}"

    @staticmethod
    def _status_for_command(command: CommandName) -> SessionStatus:
        mapping = {
            CommandName.POST_BY_INSPIRATION: SessionStatus.GENERATING_POST,
            CommandName.QUOTE: SessionStatus.GENERATING_QUOTE,
            CommandName.COMMENT: SessionStatus.GENERATING_COMMENT,
        }
        return mapping[command]

    @staticmethod
    def _purpose_for_command(command: CommandName) -> PostPurpose:
        mapping = {
            CommandName.POST_BY_INSPIRATION: PostPurpose.POST,
            CommandName.QUOTE: PostPurpose.QUOTE,
            CommandName.COMMENT: PostPurpose.COMMENT,
        }
        return mapping[command]

    @staticmethod
    def _creator_source_post(source_post) -> CreatorSourcePost:
        return CreatorSourcePost(
            post_id=source_post.post_id,
            source_url=source_post.post_url,
            text=source_post.text or "",
            purpose=source_post.purpose,
            media_urls=CreatorWorkflowService._valid_media_urls(source_post.media_urls or []),
            reply_context=list(source_post.reply_context or []),
            agent_sentiment=list(source_post.agent_sentiment or []),
            agent_comments=source_post.agent_comments or "",
            related_sources=list(source_post.related_sources or []),
        )

    @staticmethod
    def _command_from_session(current_session) -> CommandName | None:
        last_command = getattr(current_session, "last_command", None)
        if not last_command:
            return None
        try:
            return CommandName(last_command)
        except ValueError:
            return None

    @staticmethod
    def _unavailable_message(command: CommandName) -> str:
        return TEXT_CREATOR_SOURCE_REQUIRED.get(command, TEXT_ANALYSIS_REQUIRED)

    @staticmethod
    def _creator_images(context: CreatorContext) -> list[Image]:
        return [Image(url=url) for url in context.source_post.media_urls]

    @staticmethod
    def _valid_media_urls(media_urls: list[str]) -> list[str]:
        return [
            url
            for url in media_urls[:CREATOR_SOURCE_MEDIA_LIMIT]
            if isinstance(url, str) and url.startswith(ALLOWED_URL_PREFIXES)
        ]
