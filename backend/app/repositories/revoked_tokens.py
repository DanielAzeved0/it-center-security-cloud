from datetime import datetime

from app.database import get_connection


def revoke_token(token_hash: str, expires_at: datetime) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO revoked_tokens (token_hash, expires_at)
            VALUES (%s, %s)
            ON CONFLICT (token_hash) DO NOTHING
            """,
            (token_hash, expires_at),
        )


def is_token_revoked(token_hash: str) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT 1 FROM revoked_tokens WHERE token_hash = %s
            """,
            (token_hash,),
        ).fetchone()
        return row is not None


def purge_expired_revoked_tokens() -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM revoked_tokens WHERE expires_at < NOW()
            """
        )
        return cursor.rowcount
