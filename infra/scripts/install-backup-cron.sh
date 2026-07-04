#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ENV_FILE="$PROJECT_ROOT/.env.production"
BACKUP_SCRIPT="$PROJECT_ROOT/infra/scripts/backup.sh"
CRON_FILE="${CRON_FILE:-/etc/cron.d/itcenter-postgres-backup}"
CRON_USER="${CRON_USER:-root}"
BACKUP_DIR="${BACKUP_DIR:-/opt/itcenter/backups}"
LOG_FILE="${LOG_FILE:-/opt/itcenter/logs/postgres-backup.log}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
BACKUP_HOUR="${BACKUP_HOUR:-2}"
BACKUP_MINUTE="${BACKUP_MINUTE:-15}"

fail() {
  printf 'FAIL %s\n' "$1" >&2
  exit 1
}

case "$(id -u)" in
  0) ;;
  *) fail "Execute como root para escrever em $CRON_FILE." ;;
esac

[ -f "$ENV_FILE" ] || fail ".env.production nao encontrado."
[ -f "$BACKUP_SCRIPT" ] || fail "backup.sh nao encontrado."
command -v cron >/dev/null 2>&1 || command -v crond >/dev/null 2>&1 || fail "cron nao encontrado."
command -v docker >/dev/null 2>&1 || fail "docker nao encontrado."

case "$BACKUP_HOUR" in
  ''|*[!0-9]*) fail "BACKUP_HOUR precisa ser numerico." ;;
esac

case "$BACKUP_MINUTE" in
  ''|*[!0-9]*) fail "BACKUP_MINUTE precisa ser numerico." ;;
esac

[ "$BACKUP_HOUR" -ge 0 ] && [ "$BACKUP_HOUR" -le 23 ] || fail "BACKUP_HOUR deve ficar entre 0 e 23."
[ "$BACKUP_MINUTE" -ge 0 ] && [ "$BACKUP_MINUTE" -le 59 ] || fail "BACKUP_MINUTE deve ficar entre 0 e 59."

mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"
chmod 600 "$LOG_FILE"

tmp_file=$(mktemp)
cat > "$tmp_file" <<EOF
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

${BACKUP_MINUTE} ${BACKUP_HOUR} * * * ${CRON_USER} cd ${PROJECT_ROOT} && BACKUP_DIR=${BACKUP_DIR} RETENTION_DAYS=${RETENTION_DAYS} sh infra/scripts/backup.sh >> ${LOG_FILE} 2>&1
EOF

install -m 0644 "$tmp_file" "$CRON_FILE"
rm -f "$tmp_file"

printf 'OK  Backup periodico instalado em %s\n' "$CRON_FILE"
printf 'OK  Agendamento diario: %s:%s UTC\n' "$BACKUP_HOUR" "$BACKUP_MINUTE"
printf 'OK  Backups: %s\n' "$BACKUP_DIR"
printf 'OK  Logs: %s\n' "$LOG_FILE"
