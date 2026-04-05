from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AIAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    stats_snapshot: str
    recommendation: str
    created_at: datetime
