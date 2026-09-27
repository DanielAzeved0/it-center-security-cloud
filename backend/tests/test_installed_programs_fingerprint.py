import pytest

from app.database import get_connection
from app.repositories.machines import (
    calculate_installed_programs_hash,
    compute_installed_programs_hash,
    save_machine_checkin,
    update_machine_installed_programs,
)
from app.schemas.agent import AgentCheckinRequest, InstalledProgramPayload, SecurityPayload


def _make_payload(
    hostname: str,
    ip_address: str,
    mac_address: str,
    programs: list[InstalledProgramPayload],
) -> AgentCheckinRequest:
    return AgentCheckinRequest(
        hostname=hostname,
        ip_address=ip_address,
        mac_address=mac_address,
        os_version="Windows 11",
        cpu_usage=15.0,
        ram_usage=45.0,
        disk_usage=55.0,
        uptime_seconds=3600,
        installed_programs=programs,
        security=SecurityPayload(
            firewall_enabled=True,
            defender_enabled=True,
            rdp_enabled=False,
        ),
    )


def test_compute_installed_programs_hash_deterministic():
    p1 = [
        InstalledProgramPayload(name="App A", version="1.0", publisher="Pub A"),
        InstalledProgramPayload(name="App B", version="2.0", publisher="Pub B"),
    ]
    p2 = [
        InstalledProgramPayload(name="App B", version="2.0", publisher="Pub B"),
        InstalledProgramPayload(name="App A", version="1.0", publisher="Pub A"),
    ]
    assert compute_installed_programs_hash(p1) == compute_installed_programs_hash(p2)
    assert calculate_installed_programs_hash(p1) == compute_installed_programs_hash(p1)


def test_compute_installed_programs_hash_handles_none_and_whitespace():
    p1 = [InstalledProgramPayload(name="  app a  ", version=None, publisher=None)]
    p2 = [InstalledProgramPayload(name="APP A", version="", publisher="")]
    assert compute_installed_programs_hash(p1) == compute_installed_programs_hash(p2)


def test_save_machine_checkin_skips_unchanged_installed_programs():
    programs = [InstalledProgramPayload(name="App 1", version="1.0", publisher="Pub 1")]
    payload1 = _make_payload("FP-TEST-01", "10.0.0.1", "00:11:22:33:44:55", programs)

    summary1, secret1 = save_machine_checkin(payload1)

    with get_connection() as conn:
        row = conn.execute(
            "SELECT installed_programs_hash FROM machines WHERE id = %s",
            (summary1.id,),
        ).fetchone()
        assert row["installed_programs_hash"] is not None
        assert row["installed_programs_hash"] == compute_installed_programs_hash(programs)

        progs_before = conn.execute(
            "SELECT id, name FROM installed_programs WHERE machine_id = %s",
            (summary1.id,),
        ).fetchall()
        assert len(progs_before) == 1
        initial_prog_id = progs_before[0]["id"]

    # Salvar segundo checkin identico
    payload1.agent_secret = secret1
    summary2, _ = save_machine_checkin(payload1)
    assert summary1.id == summary2.id

    with get_connection() as conn:
        row2 = conn.execute(
            "SELECT installed_programs_hash FROM machines WHERE id = %s",
            (summary1.id,),
        ).fetchone()
        assert row2["installed_programs_hash"] == row["installed_programs_hash"]

        # Confirm program was not deleted and re-inserted (id remains unchanged)
        progs_after = conn.execute(
            "SELECT id, name FROM installed_programs WHERE machine_id = %s",
            (summary1.id,),
        ).fetchall()
        assert len(progs_after) == 1
        assert progs_after[0]["id"] == initial_prog_id


def test_save_machine_checkin_updates_when_installed_programs_change():
    programs1 = [InstalledProgramPayload(name="App 1", version="1.0", publisher="Pub 1")]
    payload1 = _make_payload("FP-TEST-02", "10.0.0.2", "00:11:22:33:44:66", programs1)
    summary1, secret1 = save_machine_checkin(payload1)

    programs2 = [
        InstalledProgramPayload(name="App 1", version="1.0", publisher="Pub 1"),
        InstalledProgramPayload(name="App 2", version="2.0", publisher="Pub 2"),
    ]
    payload2 = _make_payload("FP-TEST-02", "10.0.0.2", "00:11:22:33:44:66", programs2)
    payload2.agent_secret = secret1
    summary2, _ = save_machine_checkin(payload2)
    assert summary1.id == summary2.id

    with get_connection() as conn:
        row = conn.execute(
            "SELECT installed_programs_hash FROM machines WHERE id = %s",
            (summary1.id,),
        ).fetchone()
        assert row["installed_programs_hash"] == compute_installed_programs_hash(programs2)
        progs = conn.execute(
            "SELECT name FROM installed_programs WHERE machine_id = %s ORDER BY name",
            (summary1.id,),
        ).fetchall()
        assert [p["name"] for p in progs] == ["App 1", "App 2"]


def test_update_machine_installed_programs_direct():
    payload = _make_payload("FP-TEST-03", "10.0.0.3", "00:11:22:33:44:77", [])
    summary, _ = save_machine_checkin(payload)

    new_progs = [InstalledProgramPayload(name="Standalone App", version="1.0", publisher="Standalone Pub")]
    update_machine_installed_programs(summary.id, new_progs)

    with get_connection() as conn:
        row = conn.execute("SELECT installed_programs_hash FROM machines WHERE id = %s", (summary.id,)).fetchone()
        assert row["installed_programs_hash"] == compute_installed_programs_hash(new_progs)
        progs = conn.execute("SELECT name FROM installed_programs WHERE machine_id = %s", (summary.id,)).fetchall()
        assert len(progs) == 1
        assert progs[0]["name"] == "Standalone App"


def test_update_machine_installed_programs_with_connection():
    payload = _make_payload("FP-TEST-04", "10.0.0.4", "00:11:22:33:44:88", [])
    summary, _ = save_machine_checkin(payload)

    new_progs = [InstalledProgramPayload(name="Explicit Conn App", version="2.0", publisher="Explicit Pub")]
    with get_connection() as conn:
        with conn.transaction():
            update_machine_installed_programs(summary.id, new_progs, connection=conn)

    with get_connection() as conn:
        row = conn.execute("SELECT installed_programs_hash FROM machines WHERE id = %s", (summary.id,)).fetchone()
        assert row["installed_programs_hash"] == compute_installed_programs_hash(new_progs)
        progs = conn.execute("SELECT name FROM installed_programs WHERE machine_id = %s", (summary.id,)).fetchall()
        assert len(progs) == 1
        assert progs[0]["name"] == "Explicit Conn App"

