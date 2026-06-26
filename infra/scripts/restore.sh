#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ENV_FILE="$PROJECT_ROOT/.env.production"
BACKUP_FILE="${1:-}"

[ -n "$BACKUP_FILE" ] || {
  printf 'Uso: %s /opt/itcenter/backups/arquivo.sql.gz\n' "$0" >&2
  exit 1
}

[ -f "$BACKUP_FILE" ] || {
  printf 'Backup nao encontrado: %s\n' "$BACKUP_FILE" >&2
  exit 1
}

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

if [ "${ITCENTER_RESTORE_CONFIRM:-}" != "YES" ]; then
  printf 'Restore sobrescreve dados do banco %s.\n' "$POSTGRES_DB" >&2
  printf 'Execute com ITCENTER_RESTORE_CONFIRM=YES para confirmar.\n' >&2
  exit 1
fi

printf 'Restaurando %s em %s...\n' "$BACKUP_FILE" "$POSTGRES_DB"
docker exec -i itcenter-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
gzip -dc "$BACKUP_FILE" | docker exec -i itcenter-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
printf 'Restore concluido.\n'
