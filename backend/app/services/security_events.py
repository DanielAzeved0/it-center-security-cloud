from app.repositories.security_events import list_security_events
from app.schemas.security_event import SecurityEventSummary


def list_registered_security_events() -> list[SecurityEventSummary]:
    return list_security_events()
