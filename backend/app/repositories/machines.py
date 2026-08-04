from app.schemas.agent import AgentCheckinRequest
from app.schemas.machine import MachineDetail, MachineLocalAdmin, MachineMetric, MachineProgram, MachineSummary
from app.database import get_connection
from psycopg.types.json import Jsonb


OFFLINE_THRESHOLD_MINUTES = 10


def save_machine_checkin(payload: AgentCheckinRequest) -> MachineSummary:
    hostname = payload.hostname.strip().upper()

    with get_connection() as connection:
        with connection.transaction():
            machine_row = connection.execute(
                """
                INSERT INTO machines (
                    hostname,
                    username,
                    ip_address,
                    operating_system,
                    os_version,
                    status,
                    last_seen
                )
                VALUES (%s, %s, %s, %s, %s, 'online', now())
                ON CONFLICT (hostname)
                DO UPDATE SET
                    username = EXCLUDED.username,
                    ip_address = EXCLUDED.ip_address,
                    operating_system = EXCLUDED.operating_system,
                    os_version = EXCLUDED.os_version,
                    status = 'online',
                    last_seen = now()
                RETURNING id, hostname, username, host(ip_address) AS ip_address, status, last_seen
                """,
                (
                    hostname,
                    payload.username,
                    payload.ip_address,
                    payload.operating_system,
                    payload.os_version,
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

            return MachineSummary(**machine_row)


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
                operating_system,
                os_version,
                status,
                last_seen,
                rustdesk_id,
                snipeit_asset_id
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


def update_machine_snipeit_asset_id(machine_id: int, snipeit_asset_id: int) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE machines
            SET snipeit_asset_id = %s
            WHERE id = %s
            """,
            (snipeit_asset_id, machine_id),
        )


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
