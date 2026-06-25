from fastapi import APIRouter

from app.schemas.alert import AlertSummary
from app.services.alerts import list_registered_alerts

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertSummary])
def list_alerts() -> list[AlertSummary]:
    return list_registered_alerts()
