#!/bin/sh
# 02-packages.sh - instala ferramentas basicas necessarias ao restante do
# bootstrap e a operacao do host. Ver docs/deployment/BOOTSTRAP.md.
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "02-packages.sh: precisa rodar como root" >&2
  exit 1
fi

echo "02-packages.sh: instalando pacotes basicos"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y \
  curl \
  git \
  ca-certificates \
  gnupg \
  ufw \
  openssl

echo "02-packages.sh: instalando Docker Scout CLI"
# Necessario para o gate de CVE (infra/scripts/docker-scout-gate.sh).
# A autenticacao no Docker Hub (docker login) e um passo manual pos-provisionamento
# que requer credenciais — nao automatizavel aqui sem expor secrets.
curl -sSfL https://raw.githubusercontent.com/docker/scout-cli/main/install.sh | sh -s -- -b /usr/local/bin
docker scout version

echo "02-packages.sh: concluido"
