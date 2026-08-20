from fastapi import APIRouter, Depends, Query

from app.schemas.security_event import SecurityEventSummary
from app.services.auth import CurrentUser, require_roles
from app.services.security_events import list_registered_security_events

router = APIRouter(prefix="/api/v1/security-events", tags=["security-events"])


@router.get("", response_model=list[SecurityEventSummary])
def list_security_events(
    machine_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_roles("admin", "analyst", "viewer")),
) -> list[SecurityEventSummary]:
    return list_registered_security_events(machine_id=machine_id, limit=limit, offset=offset)
