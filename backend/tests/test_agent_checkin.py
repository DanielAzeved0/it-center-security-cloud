from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app


VALID_PAYLOAD = {
    "hostname": "PC-FINANCEIRO-01",
    "username": "daniel",
    "ip_address": "192.168.15.25",
    "operating_system": "Windows 11 Pro",
    "os_version": "23H2",
    "cpu_usage": 22.5,
    "ram_usage": 61.2,
    "disk_usage": 74.8,
    "uptime_seconds": 86400,
    "installed_programs": [
        {
            "name": "Google Chrome",
            "version": "126.0",
            "publisher": "Google",
        }
    ],
    "security": {
        "firewall_enabled": True,
        "defender_enabled": True,
        "rdp_enabled": False,
        "local_admins": ["Administrator", "Daniel"],
        "usb_devices": [],
        "failed_logins_last_hour": 0,
    },
}


def test_agent_checkin_accepts_valid_payload(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Check-in received",
        "machine_id": 1,
    }


def test_agent_checkin_persists_machine_metrics_and_programs(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    assert response.status_code == 200

    with get_connection() as connection:
        machine_count = connection.execute("SELECT count(*) FROM machines").fetchone()["count"]
        metric_count = connection.execute("SELECT count(*) FROM metrics").fetchone()["count"]
        program_count = connection.execute("SELECT count(*) FROM installed_programs").fetchone()["count"]
        agent_config_count = connection.execute("SELECT count(*) FROM agent_configs").fetchone()["count"]

    assert machine_count == 1
    assert metric_count == 1
    assert program_count == 1
    assert agent_config_count == 1


def test_agent_checkin_generates_soc_events_and_alerts_for_risky_posture(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {
        **VALID_PAYLOAD,
        "security": {
            **VALID_PAYLOAD["security"],
            "firewall_enabled": False,
            "defender_enabled": False,
            "rdp_enabled": True,
        },
    }

    response = client.post(
        "/api/v1/agent/checkin",
        json=payload,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    assert response.status_code == 200

    with get_connection() as connection:
        events = connection.execute(
            """
            SELECT event_type, severity, source
            FROM security_events
            ORDER BY event_type
            """
        ).fetchall()
        alerts = connection.execute(
            """
            SELECT alert_type, severity, status
            FROM alerts
            ORDER BY alert_type
            """
        ).fetchall()

    assert [event["event_type"] for event in events] == [
        "defender_disabled",
        "firewall_disabled",
        "rdp_enabled",
    ]
    assert {event["severity"] for event in events} == {"high", "medium"}
    assert {event["source"] for event in events} == {"agent"}
    assert [alert["alert_type"] for alert in alerts] == [
        "defender_disabled",
        "firewall_disabled",
        "rdp_enabled",
    ]
    assert {alert["status"] for alert in alerts} == {"open"}


def test_agent_checkin_does_not_duplicate_open_soc_alerts(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {
        **VALID_PAYLOAD,
        "security": {
            **VALID_PAYLOAD["security"],
            "firewall_enabled": False,
        },
    }

    for _ in range(2):
        response = client.post(
            "/api/v1/agent/checkin",
            json=payload,
            headers={"X-Agent-Api-Key": "test-key"},
        )
        assert response.status_code == 200

    with get_connection() as connection:
        event_count = connection.execute("SELECT count(*) FROM security_events").fetchone()["count"]
        alert_count = connection.execute("SELECT count(*) FROM alerts").fetchone()["count"]

    assert event_count == 2
    assert alert_count == 1


def test_agent_checkin_uses_local_admin_baseline_before_alerting_new_admin(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    baseline_payload = {
        **VALID_PAYLOAD,
        "security": {
            **VALID_PAYLOAD["security"],
            "local_admins": ["BUILTIN\\Administrators"],
        },
    }

    response = client.post(
        "/api/v1/agent/checkin",
        json=baseline_payload,
        headers={"X-Agent-Api-Key": "test-key"},
    )
    assert response.status_code == 200

    new_admin_payload = {
        **baseline_payload,
        "security": {
            **baseline_payload["security"],
            "local_admins": ["BUILTIN\\Administrators", "DOMAIN\\NewAdmin"],
        },
    }
    response = client.post(
        "/api/v1/agent/checkin",
        json=new_admin_payload,
        headers={"X-Agent-Api-Key": "test-key"},
    )
    assert response.status_code == 200

    with get_connection() as connection:
        events = connection.execute(
            "SELECT event_type, severity FROM security_events WHERE event_type = 'new_admin_user'"
        ).fetchall()
        alerts = connection.execute(
            "SELECT alert_type, severity, status FROM alerts WHERE alert_type = 'new_admin_user'"
        ).fetchall()

    assert len(events) == 1
    assert events[0]["severity"] == "high"
    assert len(alerts) == 1
    assert alerts[0]["status"] == "open"


def test_agent_checkin_registers_usb_event_without_alert(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {
        **VALID_PAYLOAD,
        "security": {
            **VALID_PAYLOAD["security"],
            "usb_devices": [
                {
                    "name": "Kingston DataTraveler",
                    "manufacturer": "Kingston",
                    "serial_number": "123",
                }
            ],
        },
    }

    response = client.post(
        "/api/v1/agent/checkin",
        json=payload,
        headers={"X-Agent-Api-Key": "test-key"},
    )
    assert response.status_code == 200

    with get_connection() as connection:
        event_count = connection.execute(
            "SELECT count(*) FROM security_events WHERE event_type = 'usb_detected'"
        ).fetchone()["count"]
        alert_count = connection.execute("SELECT count(*) FROM alerts").fetchone()["count"]

    assert event_count == 1
    assert alert_count == 0


def test_agent_checkin_generates_software_soc_events_and_alerts(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {
        **VALID_PAYLOAD,
        "installed_programs": [
            {"name": "RustDesk", "version": "1.2", "publisher": "RustDesk"},
            {"name": "AnyDesk", "version": "8.0", "publisher": "AnyDesk"},
            {"name": "ZeroTier One", "version": "1.14", "publisher": "ZeroTier"},
            {"name": "qBittorrent", "version": "4.6", "publisher": "qBittorrent"},
        ],
    }

    response = client.post(
        "/api/v1/agent/checkin",
        json=payload,
        headers={"X-Agent-Api-Key": "test-key"},
    )
    assert response.status_code == 200

    with get_connection() as connection:
        events = connection.execute(
            """
            SELECT event_type, severity
            FROM security_events
            ORDER BY event_type
            """
        ).fetchall()
        alerts = connection.execute(
            """
            SELECT alert_type, severity, status
            FROM alerts
            ORDER BY alert_type
            """
        ).fetchall()

    assert ("remote_access_tool_detected", "low") in [
        (event["event_type"], event["severity"])
        for event in events
    ]
    assert ("unauthorized_remote_access_tool", "medium") in [
        (event["event_type"], event["severity"])
        for event in events
    ]
    assert ("unauthorized_vpn_tool", "high") in [
        (event["event_type"], event["severity"])
        for event in events
    ]
    assert ("torrent_software_detected", "high") in [
        (event["event_type"], event["severity"])
        for event in events
    ]
    assert [alert["alert_type"] for alert in alerts] == [
        "torrent_software_detected",
        "unauthorized_remote_access_tool",
        "unauthorized_vpn_tool",
    ]


def test_agent_checkin_rejects_missing_api_key(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    response = client.post("/api/v1/agent/checkin", json=VALID_PAYLOAD)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing agent API key"}


def test_agent_checkin_rejects_invalid_payload(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {**VALID_PAYLOAD, "cpu_usage": 101}

    response = client.post(
        "/api/v1/agent/checkin",
        json=payload,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    assert response.status_code == 422
