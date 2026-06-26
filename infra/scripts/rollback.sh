#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ENV_FILE="$PROJECT_ROOT/.env.production"
COMPOSE_FILE="$PROJECT_ROOT/infra/docker-compose.production.yml"
TARGET_REF="${1:-}"

[ -n "$TARGET_REF" ] || {
  printf 'Uso: %s <git-ref-anterior>\n' "$0" >&2
  printf 'Exemplo: %s HEAD~1\n' "$0" >&2
  exit 1
}

cd "$PROJECT_ROOT"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  printf 'Este rollback precisa ser executado dentro do clone Git.\n' >&2
  exit 1
}

current_ref=$(git rev-parse --short HEAD)
target_sha=$(git rev-parse --short "$TARGET_REF")

printf 'Rollback de %s para %s.\n' "$current_ref" "$target_sha"
printf 'O volume postgres_data sera preservado.\n'

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" stop nginx frontend backend
git switch --detach "$TARGET_REF"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build backend frontend
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps
