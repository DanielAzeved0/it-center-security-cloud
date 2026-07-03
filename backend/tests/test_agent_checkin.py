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


def test_agent_checkin_persists_full_operational_snapshot(monkeypatch, auth_headers):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    assert response.status_code == 200
    machine_id = response.json()["machine_id"]

    with get_connection() as connection:
        machine = connection.execute(
            """
            SELECT
                hostname,
                username,
                host(ip_address) AS ip_address,
                operating_system,
                os_version,
                status,
                last_seen
            FROM machines
            WHERE id = %s
            """,
            (machine_id,),
        ).fetchone()
        metric = connection.execute(
            """
            SELECT
                cpu_usage::float AS cpu_usage,
                ram_usage::float AS ram_usage,
                disk_usage::float AS disk_usage,
                uptime_seconds
            FROM metrics
            WHERE machine_id = %s
            """,
            (machine_id,),
        ).fetchone()
        programs = connection.execute(
            """
            SELECT name, version, publisher
            FROM installed_programs
            WHERE machine_id = %s
            """,
            (machine_id,),
        ).fetchall()
        local_admins = connection.execute(
            """
            SELECT admin_name
            FROM machine_local_admins
            WHERE machine_id = %s
            ORDER BY admin_name
            """,
            (machine_id,),
        ).fetchall()
        agent_config = connection.execute(
            """
            SELECT
                checkin_interval_minutes,
                collect_inventory,
                collect_security,
                collect_metrics
            FROM agent_configs
            WHERE machine_id = %s
            """,
            (machine_id,),
        ).fetchone()

    assert machine == {
        "hostname": "PC-FINANCEIRO-01",
        "username": "daniel",
        "ip_address": "192.168.15.25",
        "operating_system": "Windows 11 Pro",
        "os_version": "23H2",
        "status": "online",
        "last_seen": machine["last_seen"],
    }
    assert machine["last_seen"] is not None
    assert metric == {
        "cpu_usage": 22.5,
        "ram_usage": 61.2,
        "disk_usage": 74.8,
        "uptime_seconds": 86400,
    }
    assert programs == [
        {
            "name": "Google Chrome",
            "version": "126.0",
            "publisher": "Google",
        }
    ]
    assert [admin["admin_name"] for admin in local_admins] == ["Administrator", "Daniel"]
    assert agent_config == {
        "checkin_interval_minutes": 5,
        "collect_inventory": True,
        "collect_security": True,
        "collect_metrics": True,
    }

    machine_response = client.get(f"/api/v1/machines/{machine_id}", headers=auth_headers)
    machines_response = client.get("/api/v1/machines", headers=auth_headers)
    metrics_response = client.get(f"/api/v1/machines/{machine_id}/metrics", headers=auth_headers)
    programs_response = client.get(f"/api/v1/machines/{machine_id}/programs", headers=auth_headers)
    admins_response = client.get(f"/api/v1/machines/{machine_id}/admins", headers=auth_headers)

    assert machines_response.status_code == 200
    assert machines_response.json()[0]["hostname"] == "PC-FINANCEIRO-01"
    assert machine_response.status_code == 200
    assert machine_response.json()["hostname"] == "PC-FINANCEIRO-01"
    assert metrics_response.status_code == 200
    assert metrics_response.json()[0]["uptime_seconds"] == 86400
    assert programs_response.status_code == 200
    assert programs_response.json() == [
        {
            "name": "Google Chrome",
            "version": "126.0",
            "publisher": "Google",
        }
    ]
    assert admins_response.status_code == 200
    assert [admin["admin_name"] for admin in admins_response.json()] == ["Administrator", "Daniel"]


def test_agent_checkin_generates_soc_events_and_alerts_for_risky_posture(monkeypatch, auth_headers):
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

    events_response = client.get("/api/v1/security-events", headers=auth_headers)
    alerts_response = client.get("/api/v1/alerts", headers=auth_headers)

    assert events_response.status_code == 200
    assert [event["event_type"] for event in events_response.json()] == [
        "rdp_enabled",
        "defender_disabled",
        "firewall_disabled",
    ]
    assert alerts_response.status_code == 200
    assert [alert["alert_type"] for alert in alerts_response.json()] == [
        "rdp_enabled",
        "defender_disabled",
        "firewall_disabled",
    ]


def test_agent_checkin_does_not_flag_known_asset(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    assert response.status_code == 200

    with get_connection() as connection:
        event_count = connection.execute(
            "SELECT count(*) FROM security_events WHERE event_type = 'unknown_asset'"
        ).fetchone()["count"]
        alert_count = connection.execute(
            "SELECT count(*) FROM alerts WHERE alert_type = 'unknown_asset'"
        ).fetchone()["count"]

    assert event_count == 0
    assert alert_count == 0


def test_agent_checkin_generates_unknown_asset_event_and_alert(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {**VALID_PAYLOAD, "hostname": "LAB-DESCONHECIDO-01"}

    response = client.post(
        "/api/v1/agent/checkin",
        json=payload,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    assert response.status_code == 200
    machine_id = response.json()["machine_id"]

    with get_connection() as connection:
        events = connection.execute(
            """
            SELECT machine_id, event_type, severity, source, description
            FROM security_events
            WHERE event_type = 'unknown_asset'
            """
        ).fetchall()
        alerts = connection.execute(
            """
            SELECT machine_id, alert_type, severity, status, title
            FROM alerts
            WHERE alert_type = 'unknown_asset'
            """
        ).fetchall()

    assert len(events) == 1
    assert events[0]["machine_id"] == machine_id
    assert events[0]["severity"] == "high"
    assert events[0]["source"] == "agent"
    assert "LAB-DESCONHECIDO-01" in events[0]["description"]
    assert len(alerts) == 1
    assert alerts[0]["machine_id"] == machine_id
    assert alerts[0]["severity"] == "high"
    assert alerts[0]["status"] == "open"
    assert alerts[0]["title"] == "Ativo desconhecido"


def test_agent_checkin_does_not_duplicate_unknown_asset_open_alert(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {**VALID_PAYLOAD, "hostname": "LAB-DESCONHECIDO-01"}

    for _ in range(2):
        response = client.post(
            "/api/v1/agent/checkin",
            json=payload,
            headers={"X-Agent-Api-Key": "test-key"},
        )
        assert response.status_code == 200

    with get_connection() as connection:
        event_count = connection.execute(
            "SELECT count(*) FROM security_events WHERE event_type = 'unknown_asset'"
        ).fetchone()["count"]
        alert_count = connection.execute(
            "SELECT count(*) FROM alerts WHERE alert_type = 'unknown_asset'"
        ).fetchone()["count"]

    assert event_count == 2
    assert alert_count == 1


def test_agent_checkin_normalizes_hostname_before_known_asset_check(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {**VALID_PAYLOAD, "hostname": " pc-financeiro-01 "}

    response = client.post(
        "/api/v1/agent/checkin",
        json=payload,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    assert response.status_code == 200

    with get_connection() as connection:
        machine = connection.execute("SELECT hostname FROM machines").fetchone()
        event_count = connection.execute(
            "SELECT count(*) FROM security_events WHERE event_type = 'unknown_asset'"
        ).fetchone()["count"]

    assert machine["hostname"] == "PC-FINANCEIRO-01"
    assert event_count == 0


def test_agent_checkin_registers_authorized_rdp_without_alert(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {
        **VALID_PAYLOAD,
        "hostname": "NOTE-DANIEL",
        "security": {
            **VALID_PAYLOAD["security"],
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
            SELECT event_type, severity, description
            FROM security_events
            WHERE event_type = 'rdp_enabled'
            """
        ).fetchall()
        alert_count = connection.execute(
            "SELECT count(*) FROM alerts WHERE alert_type = 'rdp_enabled'"
        ).fetchone()["count"]

    assert len(events) == 1
    assert events[0]["severity"] == "low"
    assert "maquina autorizada" in events[0]["description"]
    assert alert_count == 0


def test_agent_checkin_registers_unauthorized_rdp_with_alert(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {
        **VALID_PAYLOAD,
        "security": {
            **VALID_PAYLOAD["security"],
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
            SELECT event_type, severity, description
            FROM security_events
            WHERE event_type = 'rdp_enabled'
            """
        ).fetchall()
        alerts = connection.execute(
            """
            SELECT alert_type, severity, status, title
            FROM alerts
            WHERE alert_type = 'rdp_enabled'
            """
        ).fetchall()

    assert len(events) == 1
    assert events[0]["severity"] == "medium"
    assert "Validar autorizacao" in events[0]["description"]
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "medium"
    assert alerts[0]["status"] == "open"
    assert alerts[0]["title"] == "RDP habilitado"


def test_agent_checkin_does_not_duplicate_unauthorized_rdp_open_alert(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {
        **VALID_PAYLOAD,
        "security": {
            **VALID_PAYLOAD["security"],
            "rdp_enabled": True,
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
        event_count = connection.execute(
            "SELECT count(*) FROM security_events WHERE event_type = 'rdp_enabled'"
        ).fetchone()["count"]
        alert_count = connection.execute(
            "SELECT count(*) FROM alerts WHERE alert_type = 'rdp_enabled'"
        ).fetchone()["count"]

    assert event_count == 2
    assert alert_count == 1


def test_agent_checkin_normalizes_hostname_before_authorized_rdp_check(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {
        **VALID_PAYLOAD,
        "hostname": " note-daniel ",
        "security": {
            **VALID_PAYLOAD["security"],
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
        machine = connection.execute("SELECT hostname FROM machines").fetchone()
        events = connection.execute(
            """
            SELECT event_type, severity
            FROM security_events
            WHERE event_type = 'rdp_enabled'
            """
        ).fetchall()
        rdp_alert_count = connection.execute(
            "SELECT count(*) FROM alerts WHERE alert_type = 'rdp_enabled'"
        ).fetchone()["count"]
        unknown_asset_count = connection.execute(
            "SELECT count(*) FROM security_events WHERE event_type = 'unknown_asset'"
        ).fetchone()["count"]

    assert machine["hostname"] == "NOTE-DANIEL"
    assert len(events) == 1
    assert events[0]["severity"] == "low"
    assert rdp_alert_count == 0
    assert unknown_asset_count == 0


def test_agent_checkin_does_not_register_rdp_event_when_disabled(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    assert response.status_code == 200

    with get_connection() as connection:
        event_count = connection.execute(
            "SELECT count(*) FROM security_events WHERE event_type = 'rdp_enabled'"
        ).fetchone()["count"]
        alert_count = connection.execute(
            "SELECT count(*) FROM alerts WHERE alert_type = 'rdp_enabled'"
        ).fetchone()["count"]

    assert event_count == 0
    assert alert_count == 0


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


def test_agent_checkin_registers_authorized_remote_tool_without_alert(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {
        **VALID_PAYLOAD,
        "installed_programs": [
            {"name": "RustDesk", "version": "1.2", "publisher": "RustDesk"},
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
            SELECT event_type, severity, raw_data
            FROM security_events
            WHERE event_type = 'remote_access_tool_detected'
            """
        ).fetchall()
        alert_count = connection.execute(
            "SELECT count(*) FROM alerts WHERE alert_type = 'remote_access_tool_detected'"
        ).fetchone()["count"]

    assert len(events) == 1
    assert events[0]["severity"] == "low"
    assert events[0]["raw_data"]["category"] == "authorized_remote_tool"
    assert events[0]["raw_data"]["tool_name"] == "rustdesk"
    assert events[0]["raw_data"]["source_field"] == "installed_programs"
    assert events[0]["raw_data"]["policy_source"] == "ASSET_POLICY.md"
    assert alert_count == 0


def test_agent_checkin_detects_unauthorized_remote_tools_by_substring(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {
        **VALID_PAYLOAD,
        "installed_programs": [
            {"name": "teamviewer host", "version": "15", "publisher": "TeamViewer"},
            {"name": "UltraViewer Client", "version": "6", "publisher": "UltraViewer"},
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
            SELECT event_type, severity, raw_data
            FROM security_events
            WHERE event_type = 'unauthorized_remote_access_tool'
            ORDER BY raw_data->>'tool_name'
            """
        ).fetchall()
        alert_count = connection.execute(
            "SELECT count(*) FROM alerts WHERE alert_type = 'unauthorized_remote_access_tool'"
        ).fetchone()["count"]

    assert [(event["severity"], event["raw_data"]["tool_name"]) for event in events] == [
        ("medium", "teamviewer"),
        ("medium", "ultraviewer"),
    ]
    assert all(event["raw_data"]["category"] == "unauthorized_remote_tool" for event in events)
    assert alert_count == 1


def test_agent_checkin_detects_dual_use_tool_with_alert(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {
        **VALID_PAYLOAD,
        "installed_programs": [
            {"name": "Nmap 7.95", "version": "7.95", "publisher": "Nmap Project"},
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
            SELECT event_type, severity, raw_data
            FROM security_events
            WHERE event_type = 'suspicious_tool_detected'
            """
        ).fetchall()
        alerts = connection.execute(
            """
            SELECT alert_type, severity, status, title
            FROM alerts
            WHERE alert_type = 'suspicious_tool_detected'
            """
        ).fetchall()

    assert len(events) == 1
    assert events[0]["severity"] == "medium"
    assert events[0]["raw_data"]["tool_name"] == "nmap"
    assert events[0]["raw_data"]["category"] == "dual_use_tool"
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "medium"
    assert alerts[0]["status"] == "open"
    assert alerts[0]["title"] == "Ferramenta sensivel detectada"


def test_agent_checkin_detects_malware_or_ransomware_indicator_with_high_alert(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {
        **VALID_PAYLOAD,
        "processes": ["LockBit.exe"],
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
            SELECT event_type, severity, raw_data
            FROM security_events
            WHERE event_type = 'malware_or_ransomware_indicator'
            """
        ).fetchall()
        alerts = connection.execute(
            """
            SELECT alert_type, severity, status, title
            FROM alerts
            WHERE alert_type = 'malware_or_ransomware_indicator'
            """
        ).fetchall()

    assert len(events) == 1
    assert events[0]["severity"] == "high"
    assert events[0]["raw_data"]["tool_name"] == "lockbit"
    assert events[0]["raw_data"]["matched_value"] == "LockBit.exe"
    assert events[0]["raw_data"]["category"] == "malware_or_ransomware_indicator"
    assert events[0]["raw_data"]["source_field"] == "processes"
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "high"
    assert alerts[0]["status"] == "open"
    assert alerts[0]["title"] == "Indicador de malware ou ransomware"


def test_agent_checkin_does_not_duplicate_same_tool_from_programs_and_processes(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {
        **VALID_PAYLOAD,
        "installed_programs": [
            {"name": "AnyDesk MSI", "version": "8.0", "publisher": "AnyDesk"},
        ],
        "processes": ["anydesk.exe"],
    }

    response = client.post(
        "/api/v1/agent/checkin",
        json=payload,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    assert response.status_code == 200

    with get_connection() as connection:
        event_count = connection.execute(
            "SELECT count(*) FROM security_events WHERE event_type = 'unauthorized_remote_access_tool'"
        ).fetchone()["count"]
        alert_count = connection.execute(
            "SELECT count(*) FROM alerts WHERE alert_type = 'unauthorized_remote_access_tool'"
        ).fetchone()["count"]

    assert event_count == 1
    assert alert_count == 1


def test_agent_checkin_allows_missing_processes_without_software_detection_error(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    assert response.status_code == 200

    with get_connection() as connection:
        detection_count = connection.execute(
            """
            SELECT count(*)
            FROM security_events
            WHERE event_type IN (
                'remote_access_tool_detected',
                'unauthorized_remote_access_tool',
                'suspicious_tool_detected',
                'malware_or_ransomware_indicator'
            )
            """
        ).fetchone()["count"]

    assert detection_count == 0


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
