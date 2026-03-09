from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from telebot.db.base import Base
from telebot.db.schemas import ReplyContextItem, SourceEvidenceItem


class XUser(Base):
    __tablename__ = "x_users"

    username: Mapped[str] = mapped_column(String(255), primary_key=True)
    x_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    followers: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_bot_user: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Post(Base):
    __tablename__ = "posts"

    post_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    post_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    own_posts: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_urls: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    rank_position: Mapped[int | None] = mapped_column(nullable=True, index=True)
    rating_score: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True, index=True
    )
    primary_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    categories: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    purpose: Mapped[str | None] = mapped_column(String(32), nullable=True)
    likes_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    comment_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    reposts_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    view_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    source_query: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    reply_context: Mapped[list[ReplyContextItem] | None] = mapped_column(JSON, nullable=True)
    related_sources: Mapped[list[SourceEvidenceItem] | None] = mapped_column(JSON, nullable=True)
    author_username: Mapped[str | None] = mapped_column(
        ForeignKey("x_users.username"), nullable=True, index=True
    )
    unsafe: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    date_of_analysis: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    analysed_for_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    agent_sentiment: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    agent_comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
