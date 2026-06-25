from datetime import datetime

from pydantic import BaseModel, Field


class MachineSummary(BaseModel):
    id: int
    hostname: str = Field(..., min_length=1, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    ip_address: str | None = Field(default=None, max_length=45)
    status: str
    last_seen: datetime
