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

# Gate rigido: so as imagens que este projeto de fato constroi/controla (backend, frontend).
# Uma CVE critical/high aqui e sempre corrigivel por nos (bump de dependencia/rebuild), entao
# falhar o deploy e a resposta certa.
images="${ITCENTER_SCOUT_IMAGES:-infra-backend:latest infra-frontend:latest}"

# Risco residual ja aceito e documentado (docs/security/SECURITY.md, P1: "CVE critica/alta em
# imagem oficial sem versao corrigida disponivel") - reportado para visibilidade, mas nunca
# bloqueia o deploy. Confirmado em 2026-08-20: as 5 imagens abaixo (postgres + toda a stack de
# observabilidade da EPIC 21) tem CVEs de toolchain Go desatualizado (stdlib, golang.org/x/*)
# embutidas pelos proprios mantenedores upstream - nao ha nada que este projeto possa mudar no
# proprio Dockerfile/dependencias para corrigir, e a versao mais nova disponivel de cada uma
# (testado node-exporter v1.9.1) ainda carrega o mesmo tipo de problema. Continuam sendo
# escaneadas a cada deploy para detectar se o quadro mudar (upstream corrigir, ou uma CVE nova
# e materialmente pior aparecer), mesmo sem ser gate automatico.
accepted_risk_images="${ITCENTER_SCOUT_ACCEPTED_RISK_IMAGES:-postgres:16-alpine prom/node-exporter:v1.8.2 gcr.io/cadvisor/cadvisor:v0.49.1 prom/prometheus:v2.55.1 grafana/grafana-oss:11.1.0}"

for image in $images; do
  printf 'Verificando CVEs critical/high em %s...\n' "$image"
  docker scout cves "$image" --only-severity critical,high --exit-code
done

for image in $accepted_risk_images; do
  printf 'Verificando CVEs critical/high em %s (risco residual aceito, P1 - nao bloqueia o deploy)...\n' "$image"
  docker scout cves "$image" --only-severity critical,high || true
done

printf 'OK  Docker Scout gate aprovado.\n'
