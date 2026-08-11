from pydantic import BaseModel

from app.schemas.security_event import SecurityEventSummary


class AlertSeverityCounts(BaseModel):
    low: int = 0
    medium: int = 0
    high: int = 0
    critical: int = 0


class DashboardSummary(BaseModel):
    machines_total: int
    machines_online: int
    machines_offline: int
    alerts_open_total: int
    alerts_open_by_severity: AlertSeverityCounts
    recent_events: list[SecurityEventSummary]
