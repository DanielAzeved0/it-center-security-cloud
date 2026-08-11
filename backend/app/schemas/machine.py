from datetime import datetime

from pydantic import BaseModel, Field


class MachineSummary(BaseModel):
    id: int
    hostname: str = Field(..., min_length=1, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    ip_address: str | None = Field(default=None, max_length=45)
    status: str
    last_seen: datetime | None
    rustdesk_id: str | None = Field(default=None, max_length=50)


class MachineDetail(MachineSummary):
    operating_system: str | None = Field(default=None, max_length=255)
    os_version: str | None = Field(default=None, max_length=100)


class MachineMetric(BaseModel):
    cpu_usage: float = Field(..., ge=0, le=100)
    ram_usage: float = Field(..., ge=0, le=100)
    disk_usage: float = Field(..., ge=0, le=100)
    uptime_seconds: int = Field(..., ge=0)
    created_at: datetime


class MachineProgram(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    version: str | None = Field(default=None, max_length=100)
    publisher: str | None = Field(default=None, max_length=255)


class MachineLocalAdmin(BaseModel):
    admin_name: str = Field(..., min_length=1, max_length=255)
    first_seen_at: datetime
    last_seen_at: datetime


class MachineRustdeskUpdate(BaseModel):
    rustdesk_id: str | None = Field(default=None, max_length=50)


class MachineRustdeskUpdateResponse(BaseModel):
    status: str
    message: str
