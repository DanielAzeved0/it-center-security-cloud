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
raw_dump="$BACKUP_DIR/.itcenter-postgres-$timestamp.sql"

# Dump para arquivo intermediario (nao pipe) para capturar o exit code real
# do pg_dump/docker exec. Em sh puro (sem pipefail/PIPESTATUS), um pipe
# `pg_dump | gzip > arquivo` so propaga o exit code do gzip, que sempre
# sucede mesmo com entrada vazia.
dump_status=0
docker exec itcenter-postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$raw_dump" || dump_status=$?

if [ "$dump_status" -ne 0 ] || [ ! -s "$raw_dump" ]; then
  rm -f "$raw_dump"
  printf 'Falha ao gerar dump do PostgreSQL (exit code %s ou arquivo vazio). Nenhum backup foi criado e a retencao nao foi executada.\n' "$dump_status" >&2
  exit 1
fi

gzip -c "$raw_dump" > "$backup_file"
rm -f "$raw_dump"
chmod 600 "$backup_file"

if ! gzip -t "$backup_file"; then
  rm -f "$backup_file"
  printf 'Backup gerado esta corrompido (falhou em gzip -t): %s. Arquivo removido e a retencao nao foi executada.\n' "$backup_file" >&2
  exit 1
fi

find "$BACKUP_DIR" -type f -name 'itcenter-postgres-*.sql.gz' -mtime +"$RETENTION_DAYS" -delete

printf 'Backup criado: %s\n' "$backup_file"
printf 'Retencao aplicada: %s dias\n' "$RETENTION_DAYS"
