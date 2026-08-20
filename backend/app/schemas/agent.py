import ipaddress
from typing import Any

from pydantic import BaseModel, Field, field_validator


class InstalledProgram(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    version: str | None = Field(default=None, max_length=100)
    publisher: str | None = Field(default=None, max_length=255)


class SecurityPayload(BaseModel):
    firewall_enabled: bool
    defender_enabled: bool
    rdp_enabled: bool
    local_admins: list[str] = Field(default_factory=list)
    usb_devices: list[dict[str, Any]] = Field(default_factory=list)
    failed_logins_last_hour: int = Field(default=0, ge=0)


class AgentCheckinRequest(BaseModel):
    hostname: str = Field(..., min_length=1, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    ip_address: str | None = Field(default=None, max_length=45)
    mac_address: str | None = Field(default=None, max_length=17)
    serial_number: str | None = Field(default=None, max_length=100)
    operating_system: str | None = Field(default=None, max_length=255)
    os_version: str | None = Field(default=None, max_length=100)
    cpu_usage: float = Field(..., ge=0, le=100)
    ram_usage: float = Field(..., ge=0, le=100)
    disk_usage: float = Field(..., ge=0, le=100)
    uptime_seconds: int = Field(..., ge=0)
    installed_programs: list[InstalledProgram] = Field(default_factory=list)
    processes: list[str] = Field(default_factory=list)
    security: SecurityPayload
    agent_secret: str | None = Field(default=None, max_length=128)
    agent_version: str | None = Field(default=None, max_length=20)

    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return value

        try:
            ipaddress.ip_address(value.strip())
        except ValueError as exc:
            raise ValueError(f"ip_address invalido: {value!r}") from exc

        return value


class AgentCheckinResponse(BaseModel):
    status: str
    message: str
    machine_id: int
    agent_secret: str | None = Field(default=None)


class AgentManifestResponse(BaseModel):
    version: str
    sha256: str
    target_agent_version: str | None = Field(default=None)
