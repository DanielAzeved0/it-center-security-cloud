#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ENV_FILE="$PROJECT_ROOT/.env.production"
COMPOSE_FILE="$PROJECT_ROOT/infra/docker-compose.production.yml"
WEBROOT="${WEBROOT:-/var/www/certbot}"

fail() {
  printf 'FAIL %s\n' "$1" >&2
  exit 1
}

[ -f "$ENV_FILE" ] || fail ".env.production nao encontrado."
[ -f "$COMPOSE_FILE" ] || fail "Compose de producao ausente."
command -v docker >/dev/null 2>&1 || fail "docker nao encontrado."

extra_args=""
if [ "${TLS_RENEW_DRY_RUN:-}" = "1" ]; then
  extra_args="--dry-run"
fi

printf 'Renovando certificado TLS com Certbot...\n'
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" --profile maintenance run --rm certbot renew --webroot -w "$WEBROOT" $extra_args

printf 'Recarregando Nginx...\n'
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T nginx nginx -s reload

printf 'OK  Renovacao TLS concluida.\n'
