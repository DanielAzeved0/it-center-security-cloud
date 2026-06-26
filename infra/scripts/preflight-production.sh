#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ENV_FILE="$PROJECT_ROOT/.env.production"
COMPOSE_FILE="$PROJECT_ROOT/infra/docker-compose.production.yml"
HTPASSWD_FILE="$PROJECT_ROOT/.secrets/dashboard.htpasswd"

fail() {
  echo "ERRO: $1" >&2
  exit 1
}

[ -f "$ENV_FILE" ] || fail "Crie .env.production a partir de .env.production.example."
[ -f "$HTPASSWD_FILE" ] || fail "Crie .secrets/dashboard.htpasswd para proteger o dashboard."

for key in DOMAIN_NAME POSTGRES_PASSWORD DATABASE_URL AGENT_API_KEY; do
  value=$(grep -E "^${key}=" "$ENV_FILE" | head -n 1 | cut -d= -f2- || true)
  [ -n "$value" ] || fail "$key nao foi definido em .env.production."
  case "$value" in
    *REPLACE_WITH*|*change-me*|*replace-me*) fail "$key ainda possui um valor padrao." ;;
  esac
done

domain=$(grep -E '^DOMAIN_NAME=' "$ENV_FILE" | head -n 1 | cut -d= -f2-)
[ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ] || fail "Certificado TLS ausente para $domain."
[ -f "/etc/letsencrypt/live/$domain/privkey.pem" ] || fail "Chave TLS ausente para $domain."

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config -q
echo "Preflight de producao aprovado para $domain."
