import os
import sys

from app.database import get_connection
from app.services.auth import hash_password


def main() -> int:
    email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    name = os.getenv("ADMIN_NAME", "Admin").strip()
    password = os.getenv("ADMIN_PASSWORD", "")

    if not email or not password:
        print("ADMIN_EMAIL and ADMIN_PASSWORD must be configured.", file=sys.stderr)
        return 1

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM users WHERE lower(email) = lower(%s)",
            (email,),
        ).fetchone()

        if existing is not None:
            print(f"Admin user already exists: {email}")
            return 0

        connection.execute(
            """
            INSERT INTO users (email, name, password_hash, role, status)
            VALUES (%s, %s, %s, 'admin', 'active')
            """,
            (email, name or "Admin", hash_password(password)),
        )

    print(f"Admin user created: {email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
