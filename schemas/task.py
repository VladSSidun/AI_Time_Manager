from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

VALID_CATEGORIES = {"work", "study", "health", "personal", "other"}
VALID_STATUSES = {"pending", "completed"}


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = "other"
    estimated_minutes: Optional[int] = None
    deadline: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    estimated_minutes: Optional[int] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    description: Optional[str]
    category: str
    status: str
    estimated_minutes: Optional[int]
    deadline: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
