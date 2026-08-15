#!/bin/sh
# 01-system.sh - valida o host e prepara o sistema base.
# Ver docs/deployment/BOOTSTRAP.md. Idempotente, falha cedo se o ambiente
# nao for o esperado (Ubuntu Server, root).
set -eu

HOSTNAME_TARGET="itcenter-edge-01"
TIMEZONE_TARGET="America/Sao_Paulo"

if [ "$(id -u)" -ne 0 ]; then
  echo "01-system.sh: precisa rodar como root" >&2
  exit 1
fi

if [ ! -f /etc/os-release ] || ! grep -qi "ubuntu" /etc/os-release; then
  echo "01-system.sh: sistema nao e Ubuntu, abortando" >&2
  exit 1
fi

echo "01-system.sh: definindo hostname para ${HOSTNAME_TARGET}"
if [ "$(hostname)" != "${HOSTNAME_TARGET}" ]; then
  hostnamectl set-hostname "${HOSTNAME_TARGET}"
fi
if ! grep -q "${HOSTNAME_TARGET}" /etc/hosts; then
  echo "127.0.1.1 ${HOSTNAME_TARGET}" >> /etc/hosts
fi

echo "01-system.sh: configurando timezone para ${TIMEZONE_TARGET}"
timedatectl set-timezone "${TIMEZONE_TARGET}"

echo "01-system.sh: atualizando pacotes do sistema"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y

echo "01-system.sh: concluido"
