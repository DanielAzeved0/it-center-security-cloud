#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ENV_FILE="$PROJECT_ROOT/.env.production"
COMPOSE_FILE="$PROJECT_ROOT/infra/docker-compose.production.yml"
HTPASSWD_FILE="$PROJECT_ROOT/.secrets/dashboard.htpasswd"
MIN_DOCKER_MAJOR=24
MIN_DISK_MB="${MIN_DISK_MB:-2048}"
MIN_MEM_MB="${MIN_MEM_MB:-512}"

ok() {
  printf 'OK  %s\n' "$1"
}

fail() {
  printf 'FAIL %s\n' "$1" >&2
  exit 1
}

get_env() {
  key="$1"
  grep -E "^${key}=" "$ENV_FILE" | head -n 1 | cut -d= -f2- || true
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "$1 nao encontrado."
}

check_port_available() {
  port="$1"
  if docker ps --format '{{.Names}} {{.Ports}}' | grep -E "itcenter-nginx .*0\.0\.0\.0:${port}->|itcenter-nginx .*:::${port}->" >/dev/null 2>&1; then
    ok "Porta $port ja esta publicada pelo itcenter-nginx"
    return
  fi

  if command -v ss >/dev/null 2>&1 && ss -ltn "( sport = :$port )" | grep -q ":$port"; then
    fail "Porta $port esta ocupada por outro processo."
  fi

  ok "Porta $port disponivel"
}

printf '\nPreflight de producao - IT Center Security Cloud\n\n'

require_command docker
ok "Docker"

docker_version=$(docker version --format '{{.Server.Version}}' 2>/dev/null || true)
[ -n "$docker_version" ] || fail "Docker daemon indisponivel."
docker_major=$(printf '%s' "$docker_version" | cut -d. -f1)
[ "$docker_major" -ge "$MIN_DOCKER_MAJOR" ] || fail "Docker $docker_version abaixo do minimo esperado: $MIN_DOCKER_MAJOR.x."
ok "Docker version $docker_version"

docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 nao encontrado."
ok "Docker Compose"

available_disk_mb=$(df -Pm "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
[ "$available_disk_mb" -ge "$MIN_DISK_MB" ] || fail "Disco livre insuficiente: ${available_disk_mb}MB. Minimo: ${MIN_DISK_MB}MB."
ok "Disco livre ${available_disk_mb}MB"

available_mem_mb=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 0)
[ "$available_mem_mb" -ge "$MIN_MEM_MB" ] || fail "Memoria disponivel insuficiente: ${available_mem_mb}MB. Minimo: ${MIN_MEM_MB}MB."
ok "Memoria disponivel ${available_mem_mb}MB"

[ -f "$ENV_FILE" ] || fail "Crie .env.production a partir de .env.production.example."
[ -f "$HTPASSWD_FILE" ] || fail "Crie .secrets/dashboard.htpasswd para proteger o dashboard."
[ -f "$COMPOSE_FILE" ] || fail "Compose de producao ausente: $COMPOSE_FILE."
ok "Estrutura"
ok "Secrets"

for key in DOMAIN_NAME POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD DATABASE_URL AGENT_API_KEY; do
  value=$(get_env "$key")
  [ -n "$value" ] || fail "$key nao foi definido em .env.production."
  case "$value" in
    *REPLACE_WITH*|*change-me*|*replace-me*|*changeme*|*placeholder*|SEU_*|monitor.example.com|example.com|example.org|localhost)
      fail "$key possui placeholder ou valor invalido para producao."
      ;;
  esac
done
domain=$(get_env DOMAIN_NAME)
case "$domain" in
  *.*) ;;
  *) fail "DOMAIN_NAME precisa ser um FQDN valido." ;;
esac
ok "Environment"
ok "Domain $domain"

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config -q
ok "Compose config"

if docker network inspect itcenter-network >/dev/null 2>&1; then
  ok "Network itcenter-network"
elif docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config | grep -q 'name: itcenter-network'; then
  ok "Network itcenter-network declarada no Compose"
else
  fail "Rede itcenter-network ausente e nao declarada no Compose."
fi

check_port_available 80
check_port_available 443

[ -d /etc/letsencrypt ] || fail "/etc/letsencrypt nao existe."
[ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ] || fail "Certificado TLS ausente para $domain."
[ -f "/etc/letsencrypt/live/$domain/privkey.pem" ] || fail "Chave TLS ausente para $domain."
ok "TLS"

if docker volume inspect postgres_data >/dev/null 2>&1; then
  ok "Volume postgres_data"
elif docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config | grep -q 'postgres_data:'; then
  ok "Volume postgres_data declarado no Compose"
else
  fail "Volume postgres_data ausente e nao declarado no Compose."
fi

printf '\n'
printf 'OK  Docker\n'
printf 'OK  Docker Compose\n'
printf 'OK  Network\n'
printf 'OK  Secrets\n'
printf 'OK  Environment\n'
printf 'OK  Volumes\n'
printf 'OK  Domain\n'
printf 'OK  TLS\n'
printf 'OK  Ready for Production\n'
