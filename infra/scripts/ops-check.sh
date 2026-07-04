#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ENV_FILE="$PROJECT_ROOT/.env.production"
COMPOSE_FILE="$PROJECT_ROOT/infra/docker-compose.production.yml"
BACKUP_DIR="${BACKUP_DIR:-/opt/itcenter/backups}"
DISK_WARN_PERCENT="${DISK_WARN_PERCENT:-80}"
DISK_FAIL_PERCENT="${DISK_FAIL_PERCENT:-90}"
MEM_WARN_MB="${MEM_WARN_MB:-512}"
MEM_FAIL_MB="${MEM_FAIL_MB:-256}"
CERT_EXPIRY_WARN_DAYS="${CERT_EXPIRY_WARN_DAYS:-30}"
CERT_EXPIRY_FAIL_DAYS="${CERT_EXPIRY_FAIL_DAYS:-7}"
BACKUP_MAX_AGE_HOURS="${BACKUP_MAX_AGE_HOURS:-30}"

exit_code=0

ok() {
  printf 'OK   %s\n' "$1"
}

warn() {
  printf 'WARN %s\n' "$1" >&2
}

fail() {
  printf 'FAIL %s\n' "$1" >&2
  exit_code=1
}

get_env() {
  key="$1"
  grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | head -n 1 | cut -d= -f2- || true
}

percent_value() {
  printf '%s' "$1" | tr -d '%'
}

check_file() {
  [ -f "$1" ] && ok "$2" || fail "$2 ausente: $1"
}

check_number_threshold() {
  label="$1"
  value="$2"
  warn_limit="$3"
  fail_limit="$4"
  direction="$5"

  case "$direction" in
    high)
      if [ "$value" -ge "$fail_limit" ]; then
        fail "$label em ${value}, limite critico ${fail_limit}"
      elif [ "$value" -ge "$warn_limit" ]; then
        warn "$label em ${value}, limite de alerta ${warn_limit}"
      else
        ok "$label em ${value}"
      fi
      ;;
    low)
      if [ "$value" -le "$fail_limit" ]; then
        fail "$label em ${value}, minimo critico ${fail_limit}"
      elif [ "$value" -le "$warn_limit" ]; then
        warn "$label em ${value}, minimo de alerta ${warn_limit}"
      else
        ok "$label em ${value}"
      fi
      ;;
  esac
}

printf '\nOperacao de producao - IT Center Security Cloud\n\n'

check_file "$ENV_FILE" ".env.production"
check_file "$COMPOSE_FILE" "Compose de producao"
command -v docker >/dev/null 2>&1 && ok "Docker disponivel" || fail "docker nao encontrado"

domain=$(get_env DOMAIN_NAME)
[ -n "$domain" ] && ok "DOMAIN_NAME definido" || fail "DOMAIN_NAME ausente em .env.production"

disk_used=$(df -P "$PROJECT_ROOT" | awk 'NR==2 {print $5}')
disk_used_percent=$(percent_value "$disk_used")
check_number_threshold "Disco usado" "$disk_used_percent" "$DISK_WARN_PERCENT" "$DISK_FAIL_PERCENT" high

if [ -r /proc/meminfo ]; then
  mem_available_mb=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
  check_number_threshold "Memoria disponivel MB" "$mem_available_mb" "$MEM_WARN_MB" "$MEM_FAIL_MB" low
else
  warn "/proc/meminfo indisponivel; memoria nao verificada"
fi

if docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config -q >/dev/null 2>&1; then
  ok "Compose config valido"
else
  fail "Compose config invalido"
fi

for container in itcenter-postgres itcenter-backend itcenter-frontend itcenter-nginx; do
  status=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container" 2>/dev/null || echo missing)
  case "$status" in
    healthy|running) ok "$container $status" ;;
    missing) fail "$container ausente" ;;
    *) fail "$container $status" ;;
  esac
done

cert_file="/etc/letsencrypt/live/$domain/fullchain.pem"
if [ -f "$cert_file" ]; then
  if command -v openssl >/dev/null 2>&1; then
    fail_seconds=$((CERT_EXPIRY_FAIL_DAYS * 86400))
    warn_seconds=$((CERT_EXPIRY_WARN_DAYS * 86400))
    if ! openssl x509 -checkend "$fail_seconds" -noout -in "$cert_file" >/dev/null 2>&1; then
      fail "Certificado TLS expira em menos de ${CERT_EXPIRY_FAIL_DAYS} dias"
    elif ! openssl x509 -checkend "$warn_seconds" -noout -in "$cert_file" >/dev/null 2>&1; then
      warn "Certificado TLS expira em menos de ${CERT_EXPIRY_WARN_DAYS} dias"
    else
      ok "Certificado TLS valido por mais de ${CERT_EXPIRY_WARN_DAYS} dias"
    fi
  else
    warn "openssl nao encontrado; certificado nao verificado"
  fi
else
  fail "Certificado TLS ausente: $cert_file"
fi

if [ -d "$BACKUP_DIR" ]; then
  if find "$BACKUP_DIR" -type f -name 'itcenter-postgres-*.sql.gz' -mmin "-$((BACKUP_MAX_AGE_HOURS * 60))" | grep -q .; then
    ok "Backup recente encontrado em $BACKUP_DIR"
  else
    warn "Nenhum backup recente em $BACKUP_DIR nas ultimas ${BACKUP_MAX_AGE_HOURS}h"
  fi
else
  warn "Diretorio de backup ausente: $BACKUP_DIR"
fi

printf '\n'
if [ "$exit_code" -eq 0 ]; then
  ok "Operacao sem falhas criticas"
else
  fail "Operacao com falhas criticas"
fi

exit "$exit_code"
