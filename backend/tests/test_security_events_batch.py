from app.database import get_connection
from app.repositories.machines import save_machine_checkin
from app.repositories.security_events import create_security_events_batch, list_security_events
from app.schemas.agent import AgentCheckinRequest
from app.services.agent import process_usb_devices


def test_create_security_events_batch_empty():
    # Calling with empty list should be a no-op
    create_security_events_batch([])
    events = list_security_events(limit=10)
    assert events == []


def test_create_security_events_batch_direct():
    payload = AgentCheckinRequest(
        hostname="DIRECT-BATCH-01",
        ip_address="10.0.0.3",
        mac_address="00:11:22:33:44:77",
        os_version="Windows 11",
        cpu_usage=10.0,
        ram_usage=20.0,
        disk_usage=30.0,
        uptime_seconds=3600,
        security={"firewall_enabled": True, "defender_enabled": True, "rdp_enabled": False},
    )
    summary, _ = save_machine_checkin(payload)

    raw_events = [
        {
            "machine_id": summary.id,
            "event_type": "usb_detected",
            "severity": "low",
            "source": "agent",
            "description": "Dispositivo USB detectado na maquina DIRECT-BATCH-01: Mouse.",
            "raw_data": {"name": "Mouse"},
        },
        {
            "machine_id": summary.id,
            "event_type": "usb_detected",
            "severity": "low",
            "source": "agent",
            "description": "Dispositivo USB detectado na maquina DIRECT-BATCH-01: Teclado.",
            "raw_data": {"name": "Teclado"},
        },
    ]

    create_security_events_batch(raw_events)

    events = list_security_events(machine_id=summary.id, limit=10)
    assert len(events) == 2
    assert {e.description for e in events} == {
        "Dispositivo USB detectado na maquina DIRECT-BATCH-01: Mouse.",
        "Dispositivo USB detectado na maquina DIRECT-BATCH-01: Teclado.",
    }


def test_process_usb_devices_batches_insert():
    payload = AgentCheckinRequest(
        hostname="USB-BATCH-01",
        ip_address="10.0.0.2",
        mac_address="00:11:22:33:44:66",
        os_version="Windows 11",
        cpu_usage=15.0,
        ram_usage=25.0,
        disk_usage=35.0,
        uptime_seconds=1200,
        security={
            "firewall_enabled": True,
            "defender_enabled": True,
            "rdp_enabled": False,
            "usb_devices": [
                {"name": "Kingston DT"},
                {"name": "SanDisk Ultra"},
            ],
        },
    )
    summary, _ = save_machine_checkin(payload)
    process_usb_devices(payload, summary.id)

    events = list_security_events(limit=10)
    usb_events = [e for e in events if e.event_type == "usb_detected" and e.machine_id == summary.id]
    assert len(usb_events) == 2


def test_create_security_events_batch_with_connection():
    payload = AgentCheckinRequest(
        hostname="CONN-BATCH-01",
        ip_address="10.0.0.9",
        mac_address="00:11:22:33:44:99",
        os_version="Windows 11",
        cpu_usage=15.0,
        ram_usage=25.0,
        disk_usage=35.0,
        uptime_seconds=1200,
        security={"firewall_enabled": True, "defender_enabled": True, "rdp_enabled": False},
    )
    summary, _ = save_machine_checkin(payload)

    raw_events = [
        {
            "machine_id": summary.id,
            "event_type": "custom_audit",
            "severity": "medium",
            "source": "agent",
            "description": "Custom audit event via explicit connection.",
            "raw_data": {"action": "audit"},
        }
    ]

    with get_connection() as conn:
        with conn.transaction():
            create_security_events_batch(raw_events, connection=conn)

    events = list_security_events(machine_id=summary.id, limit=10)
    assert len(events) == 1
    assert events[0].description == "Custom audit event via explicit connection."

