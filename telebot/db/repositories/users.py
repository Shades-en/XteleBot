from datetime import date
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from telebot.common.constants import SESSION_PREFIX
from telebot.common.enums import SessionStatus
from telebot.db.app_models import AppSession, AppUser


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user(self, telegram_user_id: int) -> AppUser | None:
        result = await self.session.execute(
            select(AppUser).where(AppUser.telegram_user_id == telegram_user_id)
        )
        return result.scalar_one_or_none()

    async def ensure_user(self, telegram_user_id: int) -> AppUser:
        user = await self.get_user(telegram_user_id)
        if user is not None:
            return user
        user = AppUser(telegram_user_id=telegram_user_id)
        self.session.add(user)
        await self.session.flush()
        return user

    async def create_or_rotate_session(self, telegram_user_id: int) -> AppSession:
        user = await self.ensure_user(telegram_user_id)
        session_id = f"{SESSION_PREFIX}{uuid4().hex}"
        app_session = AppSession(
            session_id=session_id,
            telegram_user_id=telegram_user_id,
            status=SessionStatus.IDLE,
            week_anchor_date=date.today(),
        )
        self.session.add(app_session)
        user.current_session_id = session_id
        await self.session.flush()
        return app_session

    async def get_current_session(self, telegram_user_id: int) -> AppSession | None:
        user = await self.get_user(telegram_user_id)
        if user is None or user.current_session_id is None:
            return None
        result = await self.session.execute(
            select(AppSession).where(AppSession.session_id == user.current_session_id)
        )
        return result.scalar_one_or_none()

    async def ensure_current_session(self, telegram_user_id: int) -> AppSession:
        session = await self.get_current_session(telegram_user_id)
        if session is not None:
            return session
        return await self.create_or_rotate_session(telegram_user_id)

    async def set_status(
        self,
        telegram_user_id: int,
        status: SessionStatus,
        last_command: str | None = None,
    ) -> AppSession:
        app_session = await self.ensure_current_session(telegram_user_id)
        app_session.status = status
        if last_command is not None:
            app_session.last_command = last_command
        await self.session.flush()
        return app_session

    async def set_creator_state(
        self,
        telegram_user_id: int,
        creator_state: dict | None,
    ) -> AppSession:
        app_session = await self.ensure_current_session(telegram_user_id)
        app_session.creator_state = creator_state
        await self.session.flush()
        return app_session

    async def update_x_identity(
        self,
        telegram_user_id: int,
        x_username: str,
        x_id: str,
    ) -> AppUser:
        user = await self.ensure_user(telegram_user_id)
        user.x_username = x_username
        user.x_id = x_id
        await self.session.flush()
        return user

    async def get_connected_x_identities(
        self,
        usernames: list[str],
        x_ids: list[str],
    ) -> tuple[set[str], set[str]]:
        if not usernames and not x_ids:
            return set(), set()
        stmt = select(AppUser)
        if usernames:
            stmt = stmt.where(AppUser.x_username.in_(usernames) | AppUser.x_id.in_(x_ids))
        else:
            stmt = stmt.where(AppUser.x_id.in_(x_ids))
        result = await self.session.execute(stmt)
        users = result.scalars().all()
        return (
            {user.x_username for user in users if user.x_username},
            {user.x_id for user in users if user.x_id},
        )
