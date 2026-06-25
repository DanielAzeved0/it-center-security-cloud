from datetime import datetime

from pydantic import BaseModel, Field


class AlertSummary(BaseModel):
    id: int
    machine_id: int | None = None
    alert_type: str = Field(..., min_length=1, max_length=100)
    severity: str = Field(..., min_length=1, max_length=20)
    status: str = Field(..., min_length=1, max_length=20)
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    created_at: datetime
