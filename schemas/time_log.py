from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TimeLogCreate(BaseModel):
    task_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    note: Optional[str] = None
    is_pomodoro: bool = False  # власна пропозиція: підтримка Pomodoro


class TimeLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    user_id: int
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    note: Optional[str]
    is_pomodoro: bool
