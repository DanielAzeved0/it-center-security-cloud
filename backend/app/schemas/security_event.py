from datetime import datetime

from pydantic import BaseModel, Field


class SecurityEventSummary(BaseModel):
    id: int
    machine_id: int | None = None
    event_type: str = Field(..., min_length=1, max_length=100)
    severity: str = Field(..., min_length=1, max_length=20)
    source: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1)
    created_at: datetime
