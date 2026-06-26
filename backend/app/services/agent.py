from app.schemas.agent import AgentCheckinRequest, AgentCheckinResponse
from app.repositories.alerts import create_open_alert_once
from app.repositories.local_admins import sync_machine_local_admins
from app.repositories.machines import save_machine_checkin
from app.repositories.security_events import create_security_event

RDP_AUTHORIZED_HOSTNAMES = {"NOTE-DANIEL", "PC-TI-01", "PC-TI-02"}
AUTHORIZED_REMOTE_TOOLS = {"rustdesk"}
UNAUTHORIZED_REMOTE_TOOLS = {"anydesk", "teamviewer", "ultraviewer"}
UNAUTHORIZED_VPN_TOOLS = {"hamachi", "zerotier", "radmin vpn", "tailscale"}
TORRENT_TOOLS = {"utorrent", "bittorrent", "qbittorrent"}


def _record_security_detection(
    *,
    machine_id: int,
    event_type: str,
    severity: str,
    title: str,
    description: str,
    raw_data: dict,
) -> None:
    create_security_event(
        machine_id=machine_id,
        event_type=event_type,
        severity=severity,
        description=description,
        raw_data=raw_data,
    )
    create_open_alert_once(
        machine_id=machine_id,
        alert_type=event_type,
        severity=severity,
        title=title,
        description=description,
    )


def _record_security_event_only(
    *,
    machine_id: int,
    event_type: str,
    severity: str,
    description: str,
    raw_data: dict,
) -> None:
    create_security_event(
        machine_id=machine_id,
        event_type=event_type,
        severity=severity,
        description=description,
        raw_data=raw_data,
    )


def _hostname(payload: AgentCheckinRequest) -> str:
    return payload.hostname.strip().upper()


def _program_matches(program_name: str, monitored_tool: str) -> bool:
    return monitored_tool in program_name.lower()


def process_local_admins(payload: AgentCheckinRequest, machine_id: int) -> None:
    new_admins = sync_machine_local_admins(machine_id, payload.security.local_admins)

    for admin in new_admins:
        _record_security_detection(
            machine_id=machine_id,
            event_type="new_admin_user",
            severity="high",
            title="Novo administrador local",
            description=f"Novo administrador local detectado na maquina {_hostname(payload)}: {admin}.",
            raw_data={"admin_name": admin},
        )


def process_usb_devices(payload: AgentCheckinRequest, machine_id: int) -> None:
    for device in payload.security.usb_devices:
        name = str(device.get("name") or "USB device")
        _record_security_event_only(
            machine_id=machine_id,
            event_type="usb_detected",
            severity="low",
            description=f"Dispositivo USB detectado na maquina {_hostname(payload)}: {name}.",
            raw_data=device,
        )


def process_failed_logins(payload: AgentCheckinRequest, machine_id: int) -> None:
    failed_count = payload.security.failed_logins_last_hour

    if failed_count > 5:
        _record_security_detection(
            machine_id=machine_id,
            event_type="failed_login",
            severity="medium",
            title="Falhas de login elevadas",
            description=f"{failed_count} falhas de login na ultima hora na maquina {_hostname(payload)}.",
            raw_data={"failed_logins_last_hour": failed_count},
        )


def process_installed_program_rules(payload: AgentCheckinRequest, machine_id: int) -> None:
    for program in payload.installed_programs:
        program_name = program.name.strip()

        for tool in AUTHORIZED_REMOTE_TOOLS:
            if _program_matches(program_name, tool):
                _record_security_event_only(
                    machine_id=machine_id,
                    event_type="remote_access_tool_detected",
                    severity="low",
                    description=f"Ferramenta remota autorizada detectada na maquina {_hostname(payload)}: {program_name}.",
                    raw_data=program.model_dump(),
                )

        for tool in UNAUTHORIZED_REMOTE_TOOLS:
            if _program_matches(program_name, tool):
                _record_security_detection(
                    machine_id=machine_id,
                    event_type="unauthorized_remote_access_tool",
                    severity="medium",
                    title="Ferramenta remota nao autorizada",
                    description=f"Ferramenta remota nao autorizada detectada na maquina {_hostname(payload)}: {program_name}.",
                    raw_data=program.model_dump(),
                )

        for tool in UNAUTHORIZED_VPN_TOOLS:
            if _program_matches(program_name, tool):
                _record_security_detection(
                    machine_id=machine_id,
                    event_type="unauthorized_vpn_tool",
                    severity="high",
                    title="VPN nao autorizada",
                    description=f"VPN nao autorizada detectada na maquina {_hostname(payload)}: {program_name}.",
                    raw_data=program.model_dump(),
                )

        for tool in TORRENT_TOOLS:
            if _program_matches(program_name, tool):
                _record_security_detection(
                    machine_id=machine_id,
                    event_type="torrent_software_detected",
                    severity="high",
                    title="Torrent detectado",
                    description=f"Software torrent detectado na maquina {_hostname(payload)}: {program_name}.",
                    raw_data=program.model_dump(),
                )


def process_security_posture(payload: AgentCheckinRequest, machine_id: int) -> None:
    security = payload.security
    raw_data = security.model_dump()

    if not security.firewall_enabled:
        _record_security_detection(
            machine_id=machine_id,
            event_type="firewall_disabled",
            severity="high",
            title="Firewall desativado",
            description=f"Firewall desativado na maquina {_hostname(payload)}.",
            raw_data=raw_data,
        )

    if not security.defender_enabled:
        _record_security_detection(
            machine_id=machine_id,
            event_type="defender_disabled",
            severity="high",
            title="Windows Defender desativado",
            description=f"Windows Defender desativado na maquina {_hostname(payload)}.",
            raw_data=raw_data,
        )

    if security.rdp_enabled:
        if _hostname(payload) in RDP_AUTHORIZED_HOSTNAMES:
            _record_security_event_only(
                machine_id=machine_id,
                event_type="rdp_enabled",
                severity="low",
                description=f"RDP habilitado em maquina autorizada: {_hostname(payload)}.",
                raw_data=raw_data,
            )
        else:
            _record_security_detection(
                machine_id=machine_id,
                event_type="rdp_enabled",
                severity="medium",
                title="RDP habilitado",
                description=f"RDP habilitado na maquina {_hostname(payload)}. Validar autorizacao.",
                raw_data=raw_data,
            )

    process_local_admins(payload, machine_id)
    process_usb_devices(payload, machine_id)
    process_failed_logins(payload, machine_id)
    process_installed_program_rules(payload, machine_id)


def process_agent_checkin(payload: AgentCheckinRequest) -> AgentCheckinResponse:
    machine = save_machine_checkin(payload)
    process_security_posture(payload, machine.id)

    return AgentCheckinResponse(
        status="success",
        message="Check-in received",
        machine_id=machine.id,
    )
