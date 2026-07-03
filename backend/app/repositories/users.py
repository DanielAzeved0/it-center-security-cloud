from app.database import get_connection


def get_user_by_email(email: str) -> dict | None:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT id, email, name, password_hash, role, status
            FROM users
            WHERE lower(email) = lower(%s)
            LIMIT 1
            """,
            (email,),
        ).fetchone()


def get_user_by_id(user_id: int) -> dict | None:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT id, email, name, role, status
            FROM users
            WHERE id = %s
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()


def mark_user_login(user_id: int) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET last_login_at = now()
            WHERE id = %s
            """,
            (user_id,),
        )
