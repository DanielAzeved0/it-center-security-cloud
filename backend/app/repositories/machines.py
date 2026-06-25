from app.schemas.agent import AgentCheckinRequest
from app.schemas.machine import MachineSummary
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
