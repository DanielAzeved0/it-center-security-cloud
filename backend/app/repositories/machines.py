import hashlib
import hmac
import secrets

from app.schemas.agent import AgentCheckinRequest
from app.schemas.machine import MachineDetail, MachineLocalAdmin, MachineMetric, MachineProgram, MachineSummary
from app.database import get_connection
from psycopg.types.json import Jsonb


OFFLINE_THRESHOLD_MINUTES = 10


class MachineIdentityMismatch(Exception):
    def __init__(self, machine_id: int, hostname: str) -> None:
        super().__init__(f"Agent secret mismatch for machine {machine_id} ({hostname})")
        self.machine_id = machine_id
        self.hostname = hostname


def _generate_agent_secret() -> str:
    return secrets.token_urlsafe(32)


def _hash_agent_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def save_machine_checkin(payload: AgentCheckinRequest) -> tuple[MachineSummary, str | None]:
    hostname = payload.hostname.strip().upper()

    with get_connection() as connection:
        with connection.transaction():
            existing_machine = connection.execute(
                "SELECT id, agent_secret_hash FROM machines WHERE hostname = %s FOR UPDATE",
                (hostname,),
            ).fetchone()

            if existing_machine is None or existing_machine["agent_secret_hash"] is None:
                issued_secret = _generate_agent_secret()
                secret_hash_to_persist = _hash_agent_secret(issued_secret)
            else:
                provided_secret = payload.agent_secret or ""
                provided_hash = _hash_agent_secret(provided_secret)

                if not hmac.compare_digest(provided_hash, existing_machine["agent_secret_hash"]):
                    raise MachineIdentityMismatch(machine_id=existing_machine["id"], hostname=hostname)

                issued_secret = None
                secret_hash_to_persist = existing_machine["agent_secret_hash"]

            machine_row = connection.execute(
                """
                INSERT INTO machines (
                    hostname,
                    username,
                    ip_address,
                    mac_address,
                    serial_number,
                    operating_system,
                    os_version,
                    status,
                    last_seen,
                    agent_secret_hash
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'online', now(), %s)
                ON CONFLICT (hostname)
                DO UPDATE SET
                    username = EXCLUDED.username,
                    ip_address = EXCLUDED.ip_address,
                    mac_address = EXCLUDED.mac_address,
                    serial_number = EXCLUDED.serial_number,
                    operating_system = EXCLUDED.operating_system,
                    os_version = EXCLUDED.os_version,
                    status = 'online',
                    last_seen = now(),
                    agent_secret_hash = EXCLUDED.agent_secret_hash
                RETURNING id, hostname, username, host(ip_address) AS ip_address, mac_address, serial_number, status, last_seen
                """,
                (
                    hostname,
                    payload.username,
                    payload.ip_address,
                    payload.mac_address,
                    payload.serial_number,
                    payload.operating_system,
                    payload.os_version,
                    secret_hash_to_persist,
                ),
            ).fetchone()

            connection.execute(
                """
                INSERT INTO metrics (
                    machine_id,
                    cpu_usage,
                    ram_usage,
                    disk_usage,
                    uptime_seconds
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    machine_row["id"],
                    payload.cpu_usage,
                    payload.ram_usage,
                    payload.disk_usage,
                    payload.uptime_seconds,
                ),
            )

            connection.execute(
                "DELETE FROM installed_programs WHERE machine_id = %s",
                (machine_row["id"],),
            )

            if payload.installed_programs:
                with connection.cursor() as cursor:
                    cursor.executemany(
                        """
                        INSERT INTO installed_programs (
                            machine_id,
                            name,
                            version,
                            publisher
                        )
                        VALUES (%s, %s, %s, %s)
                        """,
                        [
                            (
                                machine_row["id"],
                                program.name,
                                program.version,
                                program.publisher,
                            )
                            for program in payload.installed_programs
                        ],
                    )

            connection.execute(
                """
                INSERT INTO agent_configs (machine_id)
                VALUES (%s)
                ON CONFLICT (machine_id) DO NOTHING
                """,
                (machine_row["id"],),
            )

            return MachineSummary(**machine_row), issued_secret


def list_machines() -> list[MachineSummary]:
    mark_stale_machines_offline()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                hostname,
                username,
                host(ip_address) AS ip_address,
                mac_address,
                serial_number,
                status,
                last_seen,
                rustdesk_id
            FROM machines
            ORDER BY id
            """
        ).fetchall()

    return [MachineSummary(**row) for row in rows]


def get_machine(machine_id: int) -> MachineDetail | None:
    mark_stale_machines_offline(machine_id)

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                hostname,
                username,
                host(ip_address) AS ip_address,
                mac_address,
                serial_number,
                operating_system,
                os_version,
                status,
                last_seen,
                rustdesk_id
            FROM machines
            WHERE id = %s
            """,
            (machine_id,),
        ).fetchone()

    if row is None:
        return None

    return MachineDetail(**row)


def update_machine_rustdesk_id(machine_id: int, rustdesk_id: str | None) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            """
            UPDATE machines
            SET rustdesk_id = %s
            WHERE id = %s
            RETURNING id
            """,
            (rustdesk_id, machine_id),
        ).fetchone()

    return row is not None


def list_machine_metrics(machine_id: int) -> list[MachineMetric] | None:
    if not machine_exists(machine_id):
        return None

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                cpu_usage::float AS cpu_usage,
                ram_usage::float AS ram_usage,
                disk_usage::float AS disk_usage,
                uptime_seconds,
                created_at
            FROM metrics
            WHERE machine_id = %s
            ORDER BY created_at DESC, id DESC
            """,
            (machine_id,),
        ).fetchall()

    return [MachineMetric(**row) for row in rows]


def list_machine_programs(machine_id: int) -> list[MachineProgram] | None:
    if not machine_exists(machine_id):
        return None

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                name,
                version,
                publisher
            FROM installed_programs
            WHERE machine_id = %s
            ORDER BY lower(name), lower(coalesce(version, '')), lower(coalesce(publisher, ''))
            """,
            (machine_id,),
        ).fetchall()

    return [MachineProgram(**row) for row in rows]


def list_machine_local_admins(machine_id: int) -> list[MachineLocalAdmin] | None:
    if not machine_exists(machine_id):
        return None

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                admin_name,
                first_seen_at,
                last_seen_at
            FROM machine_local_admins
            WHERE machine_id = %s
            ORDER BY lower(admin_name)
            """,
            (machine_id,),
        ).fetchall()

    return [MachineLocalAdmin(**row) for row in rows]


def machine_exists(machine_id: int) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM machines WHERE id = %s",
            (machine_id,),
        ).fetchone()

    return row is not None


def mark_stale_machines_offline(machine_id: int | None = None) -> None:
    query = """
        UPDATE machines
        SET status = 'offline'
        WHERE status <> 'offline'
          AND (
            last_seen IS NULL
            OR last_seen < now() - (%s * interval '1 minute')
          )
    """
    params: list[object] = [OFFLINE_THRESHOLD_MINUTES]

    if machine_id is not None:
        query += " AND id = %s"
        params.append(machine_id)

    query += " RETURNING id, hostname, last_seen"

    with get_connection() as connection:
        with connection.transaction():
            stale_rows = connection.execute(query, params).fetchall()

            for row in stale_rows:
                connection.execute(
                    """
                    INSERT INTO security_events (
                        machine_id,
                        event_type,
                        severity,
                        source,
                        description,
                        raw_data
                    )
                    VALUES (%s, 'machine_offline', 'low', 'system', %s, %s)
                    """,
                    (
                        row["id"],
                        f"Máquina {row['hostname']} sem check-in por mais de {OFFLINE_THRESHOLD_MINUTES} minutos.",
                        Jsonb(
                            {
                                "hostname": row["hostname"],
                                "last_seen": row["last_seen"].isoformat() if row["last_seen"] else None,
                                "offline_threshold_minutes": OFFLINE_THRESHOLD_MINUTES,
                            }
                        ),
                    ),
                )
