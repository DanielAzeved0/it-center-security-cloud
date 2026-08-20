import re

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.repositories.alerts import list_alerts
from app.repositories.security_events import list_security_events
from app.services.auth import CurrentUser, require_roles
from app.services.dashboard import get_registered_dashboard_summary
from app.services.machines import (
    get_registered_machine,
    list_registered_machine_local_admins,
    list_registered_machine_metrics,
    list_registered_machine_programs,
)
from app.services.reports import build_executive_report_pdf, build_machine_report_pdf

router = APIRouter(prefix="/api/v1", tags=["reports"])


def _safe_filename_segment(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip())
    return sanitized.strip("-") or "relatorio"


def _pdf_response(content: bytes, filename: str) -> Response:
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/reports/executive.pdf")
def get_executive_report(
    current_user: CurrentUser = Depends(require_roles("admin", "analyst", "viewer")),
) -> Response:
    summary = get_registered_dashboard_summary()
    pdf_bytes = build_executive_report_pdf(summary=summary)

    return _pdf_response(pdf_bytes, "relatorio-executivo.pdf")


@router.get("/machines/{machine_id}/report.pdf")
def get_machine_report(
    machine_id: int,
    current_user: CurrentUser = Depends(require_roles("admin", "analyst", "viewer")),
) -> Response:
    machine = get_registered_machine(machine_id)

    if machine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machine not found")

    metrics = list_registered_machine_metrics(machine_id) or []
    programs = list_registered_machine_programs(machine_id) or []
    admins = list_registered_machine_local_admins(machine_id) or []
    alerts = list_alerts(machine_id=machine_id, limit=500)
    events = list_security_events(machine_id=machine_id, limit=500)

    pdf_bytes = build_machine_report_pdf(
        machine=machine,
        metrics=metrics,
        programs=programs,
        admins=admins,
        alerts=alerts,
        events=events,
    )

    filename = f"relatorio-{_safe_filename_segment(machine.hostname.lower())}.pdf"
    return _pdf_response(pdf_bytes, filename)
