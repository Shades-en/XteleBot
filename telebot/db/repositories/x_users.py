from datetime import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from telebot.db.social_models import XUser


class XUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_username(self, username: str) -> XUser | None:
        result = await self.session.execute(
            select(XUser).where(XUser.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_usernames(self, usernames: list[str]) -> dict[str, XUser]:
        if not usernames:
            return {}
        result = await self.session.execute(
            select(XUser).where(XUser.username.in_(usernames))
        )
        return {user.username: user for user in result.scalars().all()}

    async def upsert_user(self, **values) -> XUser:
        username = values["username"]
        user = await self.get_by_username(username)
        if user is None:
            user = XUser(username=username, x_id=values["x_id"])
            self.session.add(user)
        for key, value in values.items():
            setattr(user, key, value)
        user.updated_at = datetime.utcnow()
        await self.session.flush()
        return user

    async def bulk_upsert_users(self, rows: list[dict]) -> None:
        if not rows:
            return
        deduped_rows = {row["username"]: row for row in rows if row.get("username")}
        statement = insert(XUser).values(list(deduped_rows.values()))
        update_columns = {
            "x_id": statement.excluded.x_id,
            "name": statement.excluded.name,
            "followers": statement.excluded.followers,
            "is_verified": statement.excluded.is_verified,
            "location": statement.excluded.location,
            "is_bot_user": statement.excluded.is_bot_user,
            "updated_at": statement.excluded.updated_at,
        }
        await self.session.execute(
            statement.on_conflict_do_update(
                index_elements=[XUser.username],
                set_=update_columns,
            )
        )
