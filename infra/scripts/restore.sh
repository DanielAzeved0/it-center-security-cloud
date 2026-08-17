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

printf 'Validando integridade do backup %s...\n' "$BACKUP_FILE"
if ! gzip -t "$BACKUP_FILE"; then
  printf 'Backup corrompido (falhou em gzip -t): %s. Nada foi alterado no banco.\n' "$BACKUP_FILE" >&2
  exit 1
fi

raw_restore="$(dirname "$BACKUP_FILE")/.itcenter-restore-$$.sql"

# Descompressao para arquivo intermediario (nao pipe) para capturar o exit
# code real do gzip antes de tocar no schema. Em sh puro (sem
# pipefail/PIPESTATUS), um pipe `gzip -dc | psql` so propaga o exit code
# do psql, e sem -v ON_ERROR_STOP=1 erros de SQL sao ignorados por padrao.
decompress_status=0
gzip -dc "$BACKUP_FILE" > "$raw_restore" || decompress_status=$?

if [ "$decompress_status" -ne 0 ] || [ ! -s "$raw_restore" ]; then
  rm -f "$raw_restore"
  printf 'Falha ao descomprimir o backup (exit code %s ou arquivo vazio). Nada foi alterado no banco.\n' "$decompress_status" >&2
  exit 1
fi

printf 'Backup validado. Recriando schema public...\n'
docker exec -i itcenter-postgres psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

printf 'Restaurando %s em %s...\n' "$BACKUP_FILE" "$POSTGRES_DB"
docker exec -i itcenter-postgres psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$raw_restore"
rm -f "$raw_restore"

printf 'Verificando tabelas centrais apos o restore...\n'
table_count=$(docker exec -i itcenter-postgres psql -v ON_ERROR_STOP=1 -A -t -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('machines','users','audit_logs','alerts','security_events');")
table_count=$(printf '%s' "$table_count" | tr -d '[:space:]')
case "$table_count" in
  ''|*[!0-9]*) table_count=0 ;;
esac

if [ "$table_count" -lt 5 ]; then
  printf 'Verificacao pos-restore FALHOU: apenas %s das 5 tabelas centrais (machines, users, audit_logs, alerts, security_events) foram encontradas em information_schema.tables apos o restore. Dados podem estar incompletos ou corrompidos.\n' "$table_count" >&2
  exit 1
fi

printf 'Restore concluido: %s das 5 tabelas centrais confirmadas em information_schema.tables.\n' "$table_count"
