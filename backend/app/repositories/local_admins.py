from app.database import get_connection


def sync_machine_local_admins(machine_id: int, admin_names: list[str]) -> list[str]:
    normalized_admins = sorted(
        {
            admin.strip()
            for admin in admin_names
            if admin is not None and admin.strip()
        },
        key=str.lower,
    )

    with get_connection() as connection:
        with connection.transaction():
            existing_rows = connection.execute(
                """
                SELECT admin_name
                FROM machine_local_admins
                WHERE machine_id = %s
                """,
                (machine_id,),
            ).fetchall()
            existing_admins = {row["admin_name"].lower() for row in existing_rows}
            new_admins = [
                admin
                for admin in normalized_admins
                if admin.lower() not in existing_admins
            ]

            for admin in normalized_admins:
                connection.execute(
                    """
                    INSERT INTO machine_local_admins (
                        machine_id,
                        admin_name,
                        last_seen_at
                    )
                    VALUES (%s, %s, now())
                    ON CONFLICT (machine_id, lower(admin_name))
                    DO UPDATE SET last_seen_at = now()
                    """,
                    (machine_id, admin),
                )

    if not existing_rows:
        return []

    return new_admins
