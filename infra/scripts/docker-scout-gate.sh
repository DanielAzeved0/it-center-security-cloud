#!/usr/bin/env sh
set -eu

command -v docker >/dev/null 2>&1 || {
  printf 'FAIL docker nao encontrado.\n' >&2
  exit 1
}

docker scout version >/dev/null 2>&1 || {
  printf 'FAIL Docker Scout nao encontrado ou nao autenticado.\n' >&2
  exit 1
}

images="${ITCENTER_SCOUT_IMAGES:-postgres:16-alpine infra-backend:latest infra-frontend:latest prom/node-exporter:v1.8.2 gcr.io/cadvisor/cadvisor:v0.49.1 prom/prometheus:v2.55.1 grafana/grafana-oss:11.1.0}"

for image in $images; do
  printf 'Verificando CVEs critical/high em %s...\n' "$image"
  docker scout cves "$image" --only-severity critical,high --exit-code
done

printf 'OK  Docker Scout gate aprovado.\n'
