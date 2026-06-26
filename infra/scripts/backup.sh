#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ENV_FILE="$PROJECT_ROOT/.env.production"
BACKUP_DIR="${BACKUP_DIR:-/opt/itcenter/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

[ -f "$ENV_FILE" ] || {
  printf '.env.production nao encontrado.\n' >&2
  exit 1
}

get_env() {
  key="$1"
  grep -E "^${key}=" "$ENV_FILE" | head -n 1 | cut -d= -f2- || true
}

POSTGRES_DB=$(get_env POSTGRES_DB)
POSTGRES_USER=$(get_env POSTGRES_USER)

[ -n "$POSTGRES_DB" ] || { printf 'POSTGRES_DB ausente.\n' >&2; exit 1; }
[ -n "$POSTGRES_USER" ] || { printf 'POSTGRES_USER ausente.\n' >&2; exit 1; }

mkdir -p "$BACKUP_DIR"
timestamp=$(date -u +%Y%m%dT%H%M%SZ)
backup_file="$BACKUP_DIR/itcenter-postgres-$timestamp.sql.gz"

docker exec itcenter-postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" | gzip > "$backup_file"
chmod 600 "$backup_file"

find "$BACKUP_DIR" -type f -name 'itcenter-postgres-*.sql.gz' -mtime +"$RETENTION_DAYS" -delete

printf 'Backup criado: %s\n' "$backup_file"
printf 'Retencao aplicada: %s dias\n' "$RETENTION_DAYS"
