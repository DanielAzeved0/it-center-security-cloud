from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.repositories.audit_logs import create_audit_log
from app.schemas.machine import (
    MachineDetail,
    MachineLocalAdmin,
    MachineMetric,
    MachineProgram,
    MachineRustdeskUpdate,
    MachineRustdeskUpdateResponse,
    MachineSummary,
)
from app.services.auth import CurrentUser, request_ip, require_roles
from app.services.machines import (
    get_registered_machine,
    list_registered_machine_local_admins,
    list_registered_machine_metrics,
    list_registered_machine_programs,
    list_registered_machines,
    update_registered_machine_rustdesk_id,
)

router = APIRouter(prefix="/api/v1/machines", tags=["machines"])


@router.get("", response_model=list[MachineSummary])
def list_machines(
    current_user: CurrentUser = Depends(require_roles("admin", "analyst", "viewer")),
) -> list[MachineSummary]:
    return list_registered_machines()


@router.get("/{machine_id}", response_model=MachineDetail)
def get_machine(
    machine_id: int,
    current_user: CurrentUser = Depends(require_roles("admin", "analyst", "viewer")),
) -> MachineDetail:
    machine = get_registered_machine(machine_id)

    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return machine


@router.get("/{machine_id}/metrics", response_model=list[MachineMetric])
def list_machine_metrics(
    machine_id: int,
    current_user: CurrentUser = Depends(require_roles("admin", "analyst", "viewer")),
) -> list[MachineMetric]:
    metrics = list_registered_machine_metrics(machine_id)

    if metrics is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return metrics


@router.get("/{machine_id}/programs", response_model=list[MachineProgram])
def list_machine_programs(
    machine_id: int,
    current_user: CurrentUser = Depends(require_roles("admin", "analyst", "viewer")),
) -> list[MachineProgram]:
    programs = list_registered_machine_programs(machine_id)

    if programs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return programs


@router.get("/{machine_id}/admins", response_model=list[MachineLocalAdmin])
def list_machine_local_admins(
    machine_id: int,
    current_user: CurrentUser = Depends(require_roles("admin", "analyst", "viewer")),
) -> list[MachineLocalAdmin]:
    admins = list_registered_machine_local_admins(machine_id)

    if admins is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return admins


@router.patch("/{machine_id}/rustdesk", response_model=MachineRustdeskUpdateResponse)
def update_machine_rustdesk(
    machine_id: int,
    payload: MachineRustdeskUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_roles("admin", "analyst")),
) -> MachineRustdeskUpdateResponse:
    if not update_registered_machine_rustdesk_id(machine_id, payload.rustdesk_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    create_audit_log(
        actor_user_id=current_user.id,
        action="machine.rustdesk_update",
        entity_type="machine",
        entity_id=str(machine_id),
        ip_address=request_ip(request),
        user_agent=request.headers.get("User-Agent"),
        metadata={"rustdesk_id": payload.rustdesk_id},
    )

    return MachineRustdeskUpdateResponse(
        status="success",
        message="Rustdesk ID updated",
    )
