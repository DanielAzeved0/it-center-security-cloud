from fastapi import APIRouter, HTTPException, status

from app.schemas.alert import AlertResolveResponse, AlertSummary
from app.services.alerts import list_registered_alerts, resolve_registered_alert

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertSummary])
def list_alerts() -> list[AlertSummary]:
    return list_registered_alerts()


@router.patch("/{alert_id}/resolve", response_model=AlertResolveResponse)
def resolve_alert(alert_id: int) -> AlertResolveResponse:
    if not resolve_registered_alert(alert_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    return AlertResolveResponse(
        status="success",
        message="Alert resolved",
    )
