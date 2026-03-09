from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telebot.common.constants import WEEKLY_SCHEDULE
from telebot.common.messages import TEXT_SCHEDULE_TEMPLATE
from telebot.db.repositories.users import UserRepository


class ScheduleWorkflowService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def render_schedule(self, telegram_user_id: int) -> str:
        async with self.session_factory() as session:
            users = UserRepository(session)
            current_session = await users.ensure_current_session(telegram_user_id)
            anchor = current_session.week_anchor_date or date.today()
        day_index = (date.today() - anchor).days % len(WEEKLY_SCHEDULE)
        lines = []
        for index, action in enumerate(WEEKLY_SCHEDULE):
            marker = "✅" if index == day_index else "▫️"
            lines.append(f"{marker} Day {index + 1}: {action}")
        return TEXT_SCHEDULE_TEMPLATE.format(
            lines="\n".join(lines),
            today_action=WEEKLY_SCHEDULE[day_index],
        )
