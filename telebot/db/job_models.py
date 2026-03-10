from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from telebot.common.enums import JobStatus
from telebot.db.base import Base


class WorkflowJob(Base):
    __tablename__ = "workflow_jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    command: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), index=True)
    progress_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    progress_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_cost_usd: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)
    cost_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
