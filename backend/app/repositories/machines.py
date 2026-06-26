from app.schemas.agent import AgentCheckinRequest
from app.schemas.machine import MachineDetail, MachineMetric, MachineProgram, MachineSummary
from app.database import get_connection


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
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                hostname,
                username,
                host(ip_address) AS ip_address,
                status,
                last_seen
            FROM machines
            ORDER BY id
            """
        ).fetchall()

    return [MachineSummary(**row) for row in rows]


def get_machine(machine_id: int) -> MachineDetail | None:
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
                last_seen
            FROM machines
            WHERE id = %s
            """,
            (machine_id,),
        ).fetchone()

    if row is None:
        return None

    return MachineDetail(**row)


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


def machine_exists(machine_id: int) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM machines WHERE id = %s",
            (machine_id,),
        ).fetchone()

    return row is not None
