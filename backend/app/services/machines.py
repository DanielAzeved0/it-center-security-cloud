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
    return get_machine(machine_id)


def update_registered_machine_rustdesk_id(machine_id: int, rustdesk_id: str | None) -> bool:
    return update_machine_rustdesk_id(machine_id, rustdesk_id)


def list_registered_machine_metrics(machine_id: int) -> list[MachineMetric] | None:
    return list_machine_metrics(machine_id)


def list_registered_machine_programs(machine_id: int) -> list[MachineProgram] | None:
    return list_machine_programs(machine_id)


def list_registered_machine_local_admins(machine_id: int) -> list[MachineLocalAdmin] | None:
    return list_machine_local_admins(machine_id)
