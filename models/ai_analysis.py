from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    stats_snapshot: Mapped[str] = mapped_column(String, nullable=False)  # JSON-рядок зі статистикою
    recommendation: Mapped[str] = mapped_column(String, nullable=False)  # текст від Claude
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
