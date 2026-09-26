#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ENV_FILE="$PROJECT_ROOT/.env.production"
COMPOSE_FILE="$PROJECT_ROOT/infra/docker-compose.production.yml"

get_env() {
  key="$1"
  grep -E "^${key}=" "$ENV_FILE" | head -n 1 | cut -d= -f2- || true
}

wait_for_healthy() {
  service="$1"
  container="$2"
  timeout="${3:-120}"
  elapsed=0

  printf 'Aguardando healthcheck de %s...\n' "$service"
  while [ "$elapsed" -lt "$timeout" ]; do
    status=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container" 2>/dev/null || echo missing)
    [ "$status" = "healthy" ] && return 0
    [ "$status" = "exited" ] && return 1
    sleep 5
    elapsed=$((elapsed + 5))
  done

  printf 'Timeout aguardando %s ficar healthy.\n' "$service" >&2
  return 1
}

cd "$PROJECT_ROOT"

sh infra/scripts/preflight-production.sh

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config -q

# Pausar servicos de observabilidade se estiverem ativos para liberar RAM durante o build (EPIC 39)
observability_was_running=0
if docker ps --format '{{.Names}}' | grep -qE '^itcenter-(prometheus|grafana|cadvisor|node-exporter)$'; then
  observability_was_running=1
  printf 'Pausando containers de observabilidade para o build...\n'
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" stop prometheus grafana cadvisor node_exporter 2>/dev/null || true
fi

# Build sequencial com COMPOSE_BAKE=false para evitar pico concorrente de memoria (EPIC 39)
printf 'Construindo imagem do backend...\n'
COMPOSE_BAKE=false docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build backend

printf 'Construindo imagem do frontend...\n'
COMPOSE_BAKE=false docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build frontend

# Nota: o gate de CVE para infra-backend/infra-frontend roda no CI (job scout
# em .github/workflows/ci.yml) antes de qualquer merge para main, nao aqui.
# A VM de 1GB trava ao indexar imagens locais sem indice pre-computado no
# Docker Hub. Decisao registrada em ADR-037 (docs/development/DECISIONS.md).

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d

# Reativar observabilidade se estava rodando antes do build
if [ "$observability_was_running" -eq 1 ]; then
  printf 'Reativando observabilidade...\n'
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" --profile observability up -d prometheus grafana cadvisor node_exporter 2>/dev/null || true
fi

wait_for_healthy postgres itcenter-postgres 120
wait_for_healthy backend itcenter-backend 120
wait_for_healthy frontend itcenter-frontend 120
wait_for_healthy nginx itcenter-nginx 120

domain=$(get_env DOMAIN_NAME)

printf 'Executando smoke tests...\n'
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T backend wget -q -O /dev/null http://127.0.0.1:8000/api/v1/health
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T nginx wget -q -O /dev/null http://frontend:3000/
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T nginx wget -q -O /dev/null http://127.0.0.1/healthz

printf '\nDeploy concluido.\n'
printf 'Dashboard: https://%s/\n' "$domain"
printf 'Agent check-in: https://%s/api/v1/agent/checkin\n\n' "$domain"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps
