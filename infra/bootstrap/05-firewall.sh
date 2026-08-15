#!/bin/sh
# 05-firewall.sh - configura o UFW: nega entrada por padrao, permite saida,
# libera SSH/HTTP/HTTPS e mantem portas internas (3000, 8000, 5432) sem
# exposicao publica. Ver docs/deployment/BOOTSTRAP.md.
#
# Defina ADMIN_SSH_CIDR (ex.: "203.0.113.10/32") para restringir o SSH a um
# IP/faixa administrativa especifica. Sem essa variavel, o SSH fica liberado
# para qualquer origem (0.0.0.0/0), igual as portas HTTP/HTTPS.
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "05-firewall.sh: precisa rodar como root" >&2
  exit 1
fi

echo "05-firewall.sh: configurando politicas padrao do UFW"
ufw default deny incoming
ufw default allow outgoing

if [ -n "${ADMIN_SSH_CIDR:-}" ]; then
  echo "05-firewall.sh: liberando SSH somente para ${ADMIN_SSH_CIDR}"
  ufw allow from "${ADMIN_SSH_CIDR}" to any port 22 proto tcp
else
  echo "05-firewall.sh: ADMIN_SSH_CIDR nao definido, liberando SSH para qualquer origem"
  ufw allow 22/tcp
fi

echo "05-firewall.sh: liberando HTTP (80) e HTTPS (443)"
ufw allow 80/tcp
ufw allow 443/tcp

echo "05-firewall.sh: portas internas (3000, 8000, 5432) permanecem sem regra de entrada publica"

echo "05-firewall.sh: habilitando UFW"
ufw --force enable

echo "05-firewall.sh: concluido"
