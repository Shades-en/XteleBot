from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.common.enums import CommandName, PostPurpose, SessionStatus
from telebot.common.messages import (
    TEXT_ANALYSIS_REQUIRED,
    TEXT_CREATOR_SOURCE_REQUIRED,
)
from telebot.db.repositories.posts import PostRepository
from telebot.db.repositories.users import UserRepository
from telebot.workflows.creator_session import (
    CreatorSessionState,
    initial_creator_session_state,
)


async def initialize_creator_state(
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user_id: int,
    command: CommandName,
) -> CreatorSessionState | None:
    candidates = await load_creator_candidates(
        session_factory,
        telegram_user_id,
        purpose_for_command(command),
    )
    if not candidates:
        return None
    return initial_creator_session_state(
        command=command,
        purpose=purpose_for_command(command),
        candidate_post_ids=[post.post_id for post in candidates],
    )


async def creator_state_from_session(
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user_id: int,
    current_session,
) -> CreatorSessionState | None:
    state = CreatorSessionState.from_dict(getattr(current_session, "creator_state", None))
    if state is not None:
        return state
    command = command_from_session(current_session)
    if command is None:
        return None
    state = await initialize_creator_state(session_factory, telegram_user_id, command)
    if state is None:
        return None
    await save_creator_state(session_factory, telegram_user_id, state)
    return state


async def active_creator_state(
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user_id: int,
) -> CreatorSessionState | None:
    async with session_factory() as session:
        current_session = await UserRepository(session).get_current_session(telegram_user_id)
        if current_session is None or current_session.status not in {
            SessionStatus.GENERATING_POST,
            SessionStatus.GENERATING_QUOTE,
            SessionStatus.GENERATING_COMMENT,
        }:
            return None
        return await creator_state_from_session(
            session_factory,
            telegram_user_id,
            current_session,
        )


async def posts_in_order(
    session_factory: async_sessionmaker[AsyncSession],
    post_ids: list[str],
) -> list[object]:
    async with session_factory() as session:
        posts = await PostRepository(session).get_posts(post_ids)
    return [posts[post_id] for post_id in post_ids if post_id in posts]


async def load_creator_candidates(
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user_id: int,
    purpose: PostPurpose,
) -> list[object]:
    async with session_factory() as session:
        return await PostRepository(session).creator_candidates_for_purpose(
            telegram_user_id,
            purpose,
        )


async def load_creator_style_examples(
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user_id: int,
) -> list[object]:
    async with session_factory() as session:
        return await PostRepository(session).recent_own_posts_for_creator_style(
            telegram_user_id
        )


async def load_post_by_id(
    session_factory: async_sessionmaker[AsyncSession],
    post_id: str,
):
    async with session_factory() as session:
        return await PostRepository(session).get_post(post_id)


async def save_creator_state(
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user_id: int,
    state: CreatorSessionState,
) -> None:
    async with session_factory() as session:
        await UserRepository(session).set_creator_state(telegram_user_id, state.to_dict())
        await session.commit()


async def store_draft_message_id(
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user_id: int,
    message_id: int,
) -> None:
    state = await active_creator_state(session_factory, telegram_user_id)
    if state is None:
        return
    await save_creator_state(
        session_factory,
        telegram_user_id,
        state.with_draft_message_id(message_id),
    )


def effective_user_id(message: Message, actor_user_id: int | None) -> int:
    if actor_user_id is not None:
        return actor_user_id
    return message.from_user.id


def status_for_command(command: CommandName) -> SessionStatus:
    return {
        CommandName.POST_BY_INSPIRATION: SessionStatus.GENERATING_POST,
        CommandName.QUOTE: SessionStatus.GENERATING_QUOTE,
        CommandName.COMMENT: SessionStatus.GENERATING_COMMENT,
    }[command]


def purpose_for_command(command: CommandName) -> PostPurpose:
    return {
        CommandName.POST_BY_INSPIRATION: PostPurpose.POST,
        CommandName.QUOTE: PostPurpose.QUOTE,
        CommandName.COMMENT: PostPurpose.COMMENT,
    }[command]


def command_from_session(current_session) -> CommandName | None:
    try:
        return CommandName(getattr(current_session, "last_command", ""))
    except ValueError:
        return None


def unavailable_message(command: CommandName) -> str:
    return TEXT_CREATOR_SOURCE_REQUIRED.get(command, TEXT_ANALYSIS_REQUIRED)
