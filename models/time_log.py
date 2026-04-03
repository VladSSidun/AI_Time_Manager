from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class TimeLog(Base):
    __tablename__ = "time_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # NULL = таймер активний
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    # Власна пропозиція: підтримка режиму Pomodoro (25 хв робота + 5 хв перерва)
    is_pomodoro: Mapped[bool] = mapped_column(Boolean, default=False)
