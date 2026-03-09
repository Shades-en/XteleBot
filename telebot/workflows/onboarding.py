import re

from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.common.enums import SessionStatus
from telebot.common.messages import (
    TEXT_SETUP_REQUIRED,
    TEXT_START_PROMPT,
    TEXT_X_USERNAME_CONFIRMED,
    TEXT_X_USERNAME_RETRY,
)
from telebot.db.repositories.users import UserRepository
from telebot.db.repositories.x_users import XUserRepository
from telebot.twitter.client import TwitterApiClient

USERNAME_PATTERN = re.compile(r"@([A-Za-z0-9_]{1,15})")


class OnboardingWorkflowService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        twitter_client: TwitterApiClient,
    ) -> None:
        self.session_factory = session_factory
        self.twitter_client = twitter_client

    async def start(self, message: Message) -> None:
        async with self.session_factory() as session:
            users = UserRepository(session)
            await users.ensure_user(message.from_user.id)
            await users.create_or_rotate_session(message.from_user.id)
            await users.set_status(message.from_user.id, SessionStatus.AWAITING_X_USERNAME)
            await session.commit()
        await message.answer(TEXT_START_PROMPT)

    async def handle_username_reply(self, message: Message) -> bool:
        async with self.session_factory() as session:
            users = UserRepository(session)
            current_session = await users.get_current_session(message.from_user.id)
            if current_session is None or current_session.status is not SessionStatus.AWAITING_X_USERNAME:
                return False
            username = self.extract_username(message.text or "")
            if username is None:
                await message.answer(TEXT_X_USERNAME_RETRY)
                return True
            verified_user = await self.twitter_client.get_user_by_username(username)
            if verified_user is None or verified_user.id is None or verified_user.userName is None:
                await message.answer(TEXT_X_USERNAME_RETRY)
                return True
            await users.update_x_identity(
                message.from_user.id,
                verified_user.userName,
                verified_user.id,
            )
            await users.set_status(message.from_user.id, SessionStatus.IDLE)
            x_users = XUserRepository(session)
            await x_users.upsert_user(
                username=verified_user.userName,
                x_id=verified_user.id,
                name=verified_user.name,
                followers=verified_user.followers,
                is_verified=bool(verified_user.isBlueVerified),
                location=verified_user.location,
                is_bot_user=True,
            )
            await session.commit()
        await message.answer(TEXT_X_USERNAME_CONFIRMED)
        return True

    @staticmethod
    def extract_username(text: str) -> str | None:
        match = USERNAME_PATTERN.search(text)
        if match is None:
            return None
        return match.group(1)
