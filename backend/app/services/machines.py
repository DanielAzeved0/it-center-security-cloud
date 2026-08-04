from app.core.config import get_settings
from app.repositories.machines import (
    get_machine,
    list_machine_local_admins,
    list_machine_metrics,
    list_machine_programs,
    list_machines,
    update_machine_rustdesk_id,
)
from app.schemas.machine import MachineDetail, MachineLocalAdmin, MachineMetric, MachineProgram, MachineSummary


def list_registered_machines() -> list[MachineSummary]:
    return list_machines()


def get_registered_machine(machine_id: int) -> MachineDetail | None:
    machine = get_machine(machine_id)

    if machine is None:
        return None

    settings = get_settings()

    if machine.snipeit_asset_id is not None and settings.snipeit_base_url:
        snipeit_asset_url = f"{settings.snipeit_base_url.rstrip('/')}/hardware/{machine.snipeit_asset_id}"
        return machine.model_copy(update={"snipeit_asset_url": snipeit_asset_url})

    return machine


def update_registered_machine_rustdesk_id(machine_id: int, rustdesk_id: str | None) -> bool:
    return update_machine_rustdesk_id(machine_id, rustdesk_id)


def list_registered_machine_metrics(machine_id: int) -> list[MachineMetric] | None:
    return list_machine_metrics(machine_id)


def list_registered_machine_programs(machine_id: int) -> list[MachineProgram] | None:
    return list_machine_programs(machine_id)


def list_registered_machine_local_admins(machine_id: int) -> list[MachineLocalAdmin] | None:
    return list_machine_local_admins(machine_id)
