from unittest.mock import patch
import psycopg

from app.database import get_connection
from app.repositories.local_admins import replace_machine_local_admins, sync_machine_local_admins
from app.repositories.machines import save_machine_checkin
from app.schemas.agent import AgentCheckinRequest


def make_checkin_payload(
    hostname: str = "ADMIN-BATCH-01",
    mac_address: str = "00:11:22:33:44:77",
    local_admins: list[str] | None = None,
) -> AgentCheckinRequest:
    return AgentCheckinRequest(
        hostname=hostname,
        ip_address="10.0.0.3",
        mac_address=mac_address,
        os_version="Windows 11",
        cpu_usage=10.0,
        ram_usage=20.0,
        disk_usage=30.0,
        uptime_seconds=3600,
        security={
            "firewall_enabled": True,
            "defender_enabled": True,
            "rdp_enabled": False,
            "local_admins": local_admins or [],
        },
    )


def test_sync_machine_local_admins_uses_executemany():
    payload = make_checkin_payload(
        hostname="ADMIN-BATCH-EXEC-01",
        mac_address="00:11:22:33:44:77",
    )
    summary, _ = save_machine_checkin(payload)

    orig_executemany = psycopg.Cursor.executemany
    calls = []

    def spy(self, query, params_seq):
        calls.append((query, params_seq))
        return orig_executemany(self, query, params_seq)

    with patch.object(psycopg.Cursor, "executemany", spy):
        admins = ["Administrator", "SecOps", "Support"]
        sync_machine_local_admins(summary.id, admins)

        assert len(calls) == 1
        query, params = calls[0]
        assert "INSERT INTO machine_local_admins" in query
        assert "ON CONFLICT (machine_id, lower(admin_name))" in query
        assert params == [
            (summary.id, "Administrator"),
            (summary.id, "SecOps"),
            (summary.id, "Support"),
        ]


def test_sync_machine_local_admins_batches():
    payload = make_checkin_payload(
        hostname="ADMIN-BATCH-01",
        mac_address="00:11:22:33:44:78",
    )
    summary, _ = save_machine_checkin(payload)

    # Primeira sincronizacao com multiplos admins (baseline inicial -> retorna [])
    admins = ["Administrator", "SecOps", "Support"]
    new_admins = sync_machine_local_admins(summary.id, admins)
    assert new_admins == []

    # Verificar se foram inseridos no banco
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT admin_name FROM machine_local_admins WHERE machine_id = %s ORDER BY admin_name",
            (summary.id,),
        ).fetchall()
        assert [r["admin_name"] for r in rows] == ["Administrator", "SecOps", "Support"]

    # Segunda sincronizacao adicionando novo admin
    admins.append("Auditor")
    new_detected = sync_machine_local_admins(summary.id, admins)
    assert new_detected == ["Auditor"]

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT admin_name FROM machine_local_admins WHERE machine_id = %s ORDER BY admin_name",
            (summary.id,),
        ).fetchall()
        assert [r["admin_name"] for r in rows] == ["Administrator", "Auditor", "SecOps", "Support"]


def test_sync_machine_local_admins_empty():
    payload = make_checkin_payload(
        hostname="ADMIN-BATCH-EMPTY-01",
        mac_address="00:11:22:33:44:79",
    )
    summary, _ = save_machine_checkin(payload)

    result = sync_machine_local_admins(summary.id, [])
    assert result == []


def test_sync_machine_local_admins_normalization_and_conflict_update():
    payload = make_checkin_payload(
        hostname="ADMIN-BATCH-NORM-01",
        mac_address="00:11:22:33:44:81",
    )
    summary, _ = save_machine_checkin(payload)

    # Envia com espacos e duplicacoes
    admins = ["  SecOps  ", "SecOps", "Administrator"]
    sync_machine_local_admins(summary.id, admins)

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT admin_name FROM machine_local_admins WHERE machine_id = %s ORDER BY admin_name",
            (summary.id,),
        ).fetchall()
        assert [r["admin_name"] for r in rows] == ["Administrator", "SecOps"]


def test_replace_machine_local_admins_alias():
    payload = make_checkin_payload(
        hostname="ADMIN-ALIAS-01",
        mac_address="00:11:22:33:44:80",
    )
    summary, _ = save_machine_checkin(payload)

    result = replace_machine_local_admins(summary.id, ["SuperAdmin"])
    assert result == []
