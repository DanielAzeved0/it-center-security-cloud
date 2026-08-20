from app.repositories.security_events import list_security_events
from app.schemas.security_event import SecurityEventSummary


def list_registered_security_events(
    machine_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[SecurityEventSummary]:
    return list_security_events(machine_id=machine_id, limit=limit, offset=offset)
