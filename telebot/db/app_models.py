from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from telebot.common.enums import SessionStatus
from telebot.db.base import Base


class AppUser(Base):
    __tablename__ = "app_users"

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    current_session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    x_username: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    x_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    sessions: Mapped[list["AppSession"]] = relationship(back_populates="user")


class AppSession(Base):
    __tablename__ = "app_sessions"
    __table_args__ = (UniqueConstraint("session_id", name="uq_app_sessions_session_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    telegram_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_users.telegram_user_id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus),
        default=SessionStatus.IDLE,
    )
    week_anchor_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_command: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user: Mapped[AppUser] = relationship(back_populates="sessions")
