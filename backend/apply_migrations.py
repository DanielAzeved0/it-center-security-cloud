from pathlib import Path

from app.database import get_connection


MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def apply_migrations() -> None:
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    if not migration_files:
        raise RuntimeError(f"No migration files found in {MIGRATIONS_DIR}")

    with get_connection() as connection:
        for migration_file in migration_files:
            sql = migration_file.read_text(encoding="utf-8")
            connection.execute(sql)

    print(f"Applied {len(migration_files)} migration file(s).", flush=True)


if __name__ == "__main__":
    apply_migrations()
