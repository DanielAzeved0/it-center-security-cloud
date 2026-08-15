#!/bin/sh
# 04-docker.sh - instala Docker CE, CLI, Compose Plugin e Buildx a partir do
# repositorio oficial da Docker, e habilita o servico no boot.
# Ver docs/deployment/BOOTSTRAP.md.
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "04-docker.sh: precisa rodar como root" >&2
  exit 1
fi

if command -v docker >/dev/null 2>&1; then
  echo "04-docker.sh: docker ja instalado, pulando"
  exit 0
fi

export DEBIAN_FRONTEND=noninteractive

echo "04-docker.sh: adicionando repositorio oficial da Docker"
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

. /etc/os-release
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
  > /etc/apt/sources.list.d/docker.list

echo "04-docker.sh: instalando Docker CE, CLI, Compose Plugin e Buildx"
apt-get update -y
apt-get install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

echo "04-docker.sh: habilitando o servico Docker no boot"
systemctl enable --now docker

echo "04-docker.sh: concluido"
