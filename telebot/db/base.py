from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from telebot.config import Settings


class Base(DeclarativeBase):
    pass


def create_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(settings.postgres_url, future=True, echo=False)


def create_session_factory(
    settings: Settings | None = None,
    engine: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    if engine is None:
        if settings is None:
            raise RuntimeError("Either settings or engine is required.")
        engine = create_engine(settings)
    return async_sessionmaker(bind=engine, expire_on_commit=False)
