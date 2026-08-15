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

echo "02-packages.sh: concluido"
