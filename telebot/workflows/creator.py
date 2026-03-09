from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.agents.factory import AgnoFactory
from telebot.common.constants import X_STATUS_URL_TEMPLATE
from telebot.common.enums import CommandName, SessionStatus
from telebot.common.messages import (
    TEXT_ANALYSIS_REQUIRED,
    TEXT_SETUP_REQUIRED,
    TEXT_SOURCE_POST_LINK_TEMPLATE,
)
from telebot.db.repositories.posts import PostRepository
from telebot.db.repositories.users import UserRepository


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
            posts = PostRepository(session)
            user = await users.ensure_user(telegram_user_id)
            if not user.x_username or not user.x_id:
                await message.answer(TEXT_SETUP_REQUIRED)
                return
            ranked_posts = await posts.top_safe_ranked_posts(telegram_user_id)
            if not ranked_posts:
                await message.answer(TEXT_ANALYSIS_REQUIRED)
                return
            status = self._status_for_command(command)
            await users.set_status(telegram_user_id, status, command.value)
            await session.commit()
            draft = await self._generate_draft(
                command=command,
                session_id=user.current_session_id or "",
                telegram_user_id=telegram_user_id,
                source_post=ranked_posts[0],
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
            status_to_command = {
                SessionStatus.GENERATING_POST: CommandName.POST_BY_INSPIRATION,
                SessionStatus.GENERATING_QUOTE: CommandName.QUOTE,
                SessionStatus.GENERATING_COMMENT: CommandName.COMMENT,
            }
            command = status_to_command[current_session.status]
            draft = await self._generate_draft(
                command=command,
                session_id=user.current_session_id or current_session.session_id,
                telegram_user_id=message.from_user.id,
                source_post=None,
                refinement=message.text,
            )
        await message.answer(draft)
        return True

    async def _generate_draft(
        self,
        command: CommandName,
        session_id: str,
        telegram_user_id: int,
        source_post,
        refinement: str | None = None,
    ) -> str:
        creator = self.agno_factory.build_creator_agent()
        source_text = source_post.text if source_post is not None else "Refine the last draft"
        reply_context = getattr(source_post, "reply_context", []) if source_post is not None else []
        prompt = (
            f"Command: {command.value}\n"
            f"Source post link: {self._source_post_url(source_post) or 'n/a'}\n"
            f"Source text: {source_text}\n"
            f"Reply context: {reply_context}\n"
            f"Research purpose: {getattr(source_post, 'purpose', None) or 'n/a'}\n"
            f"Research sentiment: {getattr(source_post, 'agent_sentiment', None) or []}\n"
            f"Research memo for creator: {getattr(source_post, 'agent_comments', None) or 'n/a'}\n"
            f"Grounded sources: {getattr(source_post, 'related_sources', None) or []}\n"
            f"Refinement request: {refinement or 'Create a strong first draft.'}\n"
            "Use the research memo and grounded sources to shape the output. "
            "Return the draft first, then reference the supporting source post link."
        )
        response = await creator.arun(prompt, user_id=str(telegram_user_id), session_id=session_id)
        draft = str(response.content)
        source_url = self._source_post_url(source_post)
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
    def _source_post_url(source_post) -> str | None:
        if source_post is None:
            return None
        author_username = getattr(source_post, "author_username", None)
        post_id = getattr(source_post, "post_id", None)
        if not author_username or not post_id:
            return None
        return X_STATUS_URL_TEMPLATE.format(
            author_username=author_username,
            post_id=post_id,
        )
