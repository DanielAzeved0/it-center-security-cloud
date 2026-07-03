from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.repositories.audit_logs import create_audit_log
from app.schemas.alert import AlertResolveResponse, AlertSummary
from app.services.auth import CurrentUser, request_ip, require_roles
from app.services.alerts import list_registered_alerts, resolve_registered_alert

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertSummary])
def list_alerts(
    current_user: CurrentUser = Depends(require_roles("admin", "analyst", "viewer")),
) -> list[AlertSummary]:
    return list_registered_alerts()


@router.patch("/{alert_id}/resolve", response_model=AlertResolveResponse)
def resolve_alert(
    alert_id: int,
    request: Request,
    current_user: CurrentUser = Depends(require_roles("admin", "analyst")),
) -> AlertResolveResponse:
    if not resolve_registered_alert(alert_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    create_audit_log(
        actor_user_id=current_user.id,
        action="alert.resolve",
        entity_type="alert",
        entity_id=str(alert_id),
        ip_address=request_ip(request),
        user_agent=request.headers.get("User-Agent"),
        metadata={},
    )

    return AlertResolveResponse(
        status="success",
        message="Alert resolved",
    )
