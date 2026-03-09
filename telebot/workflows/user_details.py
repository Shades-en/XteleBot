from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.common.messages import TEXT_CURRENT_USER_REQUIRED, TEXT_CURRENT_USER_TEMPLATE
from telebot.db.repositories.users import UserRepository
from telebot.db.repositories.x_users import XUserRepository


class UserDetailsWorkflowService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def render_current_user(
        self,
        telegram_user_id: int,
        telegram_display_name: str,
    ) -> str:
        async with self.session_factory() as session:
            users = UserRepository(session)
            user = await users.get_user(telegram_user_id)
            if user is None:
                return TEXT_CURRENT_USER_REQUIRED
            current_session = await users.get_current_session(telegram_user_id)
            x_display_name = "not set"
            if user.x_username:
                x_user = await XUserRepository(session).get_by_username(user.x_username)
                if x_user is not None and x_user.name:
                    x_display_name = x_user.name
        return TEXT_CURRENT_USER_TEMPLATE.format(
            telegram_user_id=user.telegram_user_id,
            telegram_display_name=telegram_display_name or "not set",
            session_id=user.current_session_id or "not set",
            status=current_session.status.value if current_session is not None else "not set",
            last_command=current_session.last_command if current_session and current_session.last_command else "not set",
            x_username=user.x_username or "not set",
            x_display_name=x_display_name,
            x_id=user.x_id or "not set",
        )
