#!/bin/sh
# bootstrap.sh - orquestra a preparacao do Edge Node na ordem oficial.
# Nao clona a aplicacao, nao preenche .env.production, nao gera secrets,
# nao emite TLS, nao sobe Docker Compose. Ver docs/deployment/BOOTSTRAP.md.
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "bootstrap.sh: precisa rodar como root" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

for step in 01-system.sh 02-packages.sh 03-directories.sh 04-docker.sh 05-firewall.sh; do
  echo "bootstrap.sh: executando ${step}"
  sh "${SCRIPT_DIR}/${step}"
done

echo "bootstrap.sh: host preparado. Siga o deploy de producao (docs/deployment/PRODUCTION.md)."
