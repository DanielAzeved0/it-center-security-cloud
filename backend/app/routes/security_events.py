from fastapi import APIRouter, Depends

from app.schemas.security_event import SecurityEventSummary
from app.services.auth import CurrentUser, require_roles
from app.services.security_events import list_registered_security_events

router = APIRouter(prefix="/api/v1/security-events", tags=["security-events"])


@router.get("", response_model=list[SecurityEventSummary])
def list_security_events(
    current_user: CurrentUser = Depends(require_roles("admin", "analyst", "viewer")),
) -> list[SecurityEventSummary]:
    return list_registered_security_events()
