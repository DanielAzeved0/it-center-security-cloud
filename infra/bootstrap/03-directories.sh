#!/bin/sh
# 03-directories.sh - cria a estrutura oficial de /opt/itcenter. Nao clona o
# repositorio nem cria secrets reais. Ver docs/deployment/BOOTSTRAP.md.
set -eu

ROOT_DIR="/opt/itcenter"

if [ "$(id -u)" -ne 0 ]; then
  echo "03-directories.sh: precisa rodar como root" >&2
  exit 1
fi

echo "03-directories.sh: criando estrutura em ${ROOT_DIR}"
for dir in app backups configs logs scripts secrets; do
  mkdir -p "${ROOT_DIR}/${dir}"
done

chmod 700 "${ROOT_DIR}/secrets"

echo "03-directories.sh: concluido"
