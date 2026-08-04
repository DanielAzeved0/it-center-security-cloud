from fastapi import BackgroundTasks

from app.schemas.agent import AgentCheckinRequest, AgentCheckinResponse
from app.repositories.alerts import create_open_alert_once
from app.repositories.local_admins import sync_machine_local_admins
from app.repositories.machines import save_machine_checkin
from app.repositories.security_events import create_security_event
from app.services.snipeit import sync_machine_asset

# Espelhos temporarios de ASSET_POLICY.md ate existir politica em banco/dashboard.
KNOWN_ASSET_HOSTNAMES = {"NOTE-DANIEL", "PC-TI-01", "PC-TI-02", "PC-FINANCEIRO-01"}
RDP_AUTHORIZED_HOSTNAMES = {"NOTE-DANIEL", "PC-TI-01", "PC-TI-02"}
AUTHORIZED_REMOTE_TOOLS = {"rustdesk"}
UNAUTHORIZED_REMOTE_TOOLS = {"anydesk", "teamviewer", "ultraviewer"}
DUAL_USE_TOOLS = {
    "advanced ip scanner",
    "angry ip scanner",
    "nmap",
    "masscan",
    "psexec",
    "paexec",
    "metasploit",
    "cobalt strike",
    "process hacker",
    "netcat",
    "nc.exe",
    "rclone",
    "megasync",
    "tor browser",
}
MALWARE_OR_RANSOMWARE_INDICATORS = {
    "mimikatz",
    "wannacry",
    "wcry",
    "lockbit",
    "blackcat",
    "alphv",
    "conti",
    "ryuk",
    "revil",
    "darkside",
}
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


def _software_detection_raw_data(
    *,
    tool_name: str,
    matched_value: str,
    category: str,
    source_field: str,
    extra: dict | None = None,
) -> dict:
    raw_data = {
        "tool_name": tool_name,
        "matched_value": matched_value,
        "category": category,
        "source_field": source_field,
        "policy_source": "ASSET_POLICY.md",
    }

    if extra:
        raw_data.update(extra)

    return raw_data


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


def process_unknown_asset(payload: AgentCheckinRequest, machine_id: int) -> None:
    hostname = _hostname(payload)

    if hostname in KNOWN_ASSET_HOSTNAMES:
        return

    _record_security_detection(
        machine_id=machine_id,
        event_type="unknown_asset",
        severity="high",
        title="Ativo desconhecido",
        description=f"Check-in recebido de ativo nao cadastrado na politica: {hostname}.",
        raw_data={"hostname": hostname, "known_assets_source": "ASSET_POLICY.md"},
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


def _process_software_value(
    *,
    payload: AgentCheckinRequest,
    machine_id: int,
    value: str,
    source_field: str,
    extra: dict | None = None,
    seen_detections: set[tuple[str, str]],
) -> None:
    software_name = value.strip()

    if not software_name:
        return

    for tool in AUTHORIZED_REMOTE_TOOLS:
        if _program_matches(software_name, tool):
            _record_security_event_only(
                machine_id=machine_id,
                event_type="remote_access_tool_detected",
                severity="low",
                description=f"Ferramenta remota autorizada detectada na maquina {_hostname(payload)}: {software_name}.",
                raw_data=_software_detection_raw_data(
                    tool_name=tool,
                    matched_value=software_name,
                    category="authorized_remote_tool",
                    source_field=source_field,
                    extra=extra,
                ),
            )

    for tool in UNAUTHORIZED_REMOTE_TOOLS:
        if _program_matches(software_name, tool):
            detection_key = ("unauthorized_remote_access_tool", tool)

            if detection_key in seen_detections:
                continue

            seen_detections.add(detection_key)
            _record_security_detection(
                machine_id=machine_id,
                event_type="unauthorized_remote_access_tool",
                severity="medium",
                title="Ferramenta remota nao autorizada",
                description=f"Ferramenta remota nao autorizada detectada na maquina {_hostname(payload)}: {software_name}.",
                raw_data=_software_detection_raw_data(
                    tool_name=tool,
                    matched_value=software_name,
                    category="unauthorized_remote_tool",
                    source_field=source_field,
                    extra=extra,
                ),
            )

    for tool in MALWARE_OR_RANSOMWARE_INDICATORS:
        if _program_matches(software_name, tool):
            detection_key = ("malware_or_ransomware_indicator", tool)

            if detection_key in seen_detections:
                continue

            seen_detections.add(detection_key)
            _record_security_detection(
                machine_id=machine_id,
                event_type="malware_or_ransomware_indicator",
                severity="high",
                title="Indicador de malware ou ransomware",
                description=f"Indicador de malware ou ransomware detectado na maquina {_hostname(payload)}: {software_name}.",
                raw_data=_software_detection_raw_data(
                    tool_name=tool,
                    matched_value=software_name,
                    category="malware_or_ransomware_indicator",
                    source_field=source_field,
                    extra=extra,
                ),
            )

    for tool in DUAL_USE_TOOLS:
        if _program_matches(software_name, tool):
            detection_key = ("suspicious_tool_detected", tool)

            if detection_key in seen_detections:
                continue

            seen_detections.add(detection_key)
            _record_security_detection(
                machine_id=machine_id,
                event_type="suspicious_tool_detected",
                severity="medium",
                title="Ferramenta sensivel detectada",
                description=f"Ferramenta sensivel ou dual-use detectada na maquina {_hostname(payload)}: {software_name}.",
                raw_data=_software_detection_raw_data(
                    tool_name=tool,
                    matched_value=software_name,
                    category="dual_use_tool",
                    source_field=source_field,
                    extra=extra,
                ),
            )


def process_installed_program_rules(payload: AgentCheckinRequest, machine_id: int) -> None:
    seen_detections: set[tuple[str, str]] = set()

    for program in payload.installed_programs:
        program_name = program.name.strip()

        _process_software_value(
            payload=payload,
            machine_id=machine_id,
            value=program_name,
            source_field="installed_programs",
            extra=program.model_dump(),
            seen_detections=seen_detections,
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

    for process_name in payload.processes:
        _process_software_value(
            payload=payload,
            machine_id=machine_id,
            value=process_name,
            source_field="processes",
            seen_detections=seen_detections,
        )


def process_security_posture(payload: AgentCheckinRequest, machine_id: int) -> None:
    security = payload.security
    raw_data = security.model_dump()

    process_unknown_asset(payload, machine_id)

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


def process_agent_checkin(payload: AgentCheckinRequest, background_tasks: BackgroundTasks) -> AgentCheckinResponse:
    machine = save_machine_checkin(payload)
    process_security_posture(payload, machine.id)
    background_tasks.add_task(sync_machine_asset, machine.id, _hostname(payload))

    return AgentCheckinResponse(
        status="success",
        message="Check-in received",
        machine_id=machine.id,
    )
