# SOC_RULES.md

# Regras de Segurança e Detecção

## Objetivo

Definir as regras de monitoramento, correlação e geração de alertas do IT Center Security Cloud.

O objetivo não é apenas detectar softwares ou eventos, mas avaliar seu contexto com base nas políticas definidas em ASSET_POLICY.md.

---

# Severidades

LOW

MEDIUM

HIGH

CRITICAL

---

# Regra 1

Falhas de Login

Evento:

failed_login

Severidade:

MEDIUM

Condição:

Mais de 5 falhas de login na ultima hora.

Ação:

Gerar alerta.

---

# Regra 2

Novo Administrador Local

Evento:

new_admin_user

Severidade:

HIGH

Condição:

Usuário adicionado ao grupo Administradores.

Ação:

Gerar alerta imediato.

---

# Regra 3

Firewall Desativado

Evento:

firewall_disabled

Severidade:

HIGH

Ação:

Gerar alerta imediato.

---

# Regra 4

Windows Defender Desativado

Evento:

defender_disabled

Severidade:

HIGH

Ação:

Gerar alerta imediato.

---

# Regra 5

RDP Habilitado

Evento:

rdp_enabled

Severidade:

MEDIUM

Ação:

Validar autorização em ASSET_POLICY.md.

Caso não autorizado:

Gerar alerta.

---

# Regra 6

USB Detectado

Evento:

usb_detected

Severidade:

LOW

Registrar:

* Usuário
* Máquina
* Horário
* Fabricante
* Serial (quando disponível)

Ação:

Somente registrar.

---

# Regra 7

Ferramentas de Acesso Remoto

Evento:

remote_access_tool_detected

Severidade:

LOW

Ferramentas monitoradas:

* RustDesk
* AnyDesk
* TeamViewer
* UltraViewer

Ação:

Registrar instalação.

Não gerar alerta automaticamente.

---

# Regra 8

Ferramenta Remota Não Autorizada

Evento:

unauthorized_remote_access_tool

Severidade:

MEDIUM

Condição:

Ferramenta instalada em máquina não autorizada.

Ação:

Gerar alerta.

---

# Regra 9

VPN Não Autorizada

Evento:

unauthorized_vpn_tool

Severidade:

HIGH

Ferramentas monitoradas:

* Hamachi
* ZeroTier
* Radmin VPN
* Tailscale

Condição:

Ferramenta instalada sem autorização.

Ação:

Gerar alerta.

---

# Regra 10

Torrent Detectado

Evento:

torrent_software_detected

Severidade:

HIGH

Ferramentas monitoradas:

* uTorrent
* BitTorrent
* qBittorrent

Ação:

Gerar alerta imediato.

---

# Regra 11

Máquina Desconhecida

Evento:

unknown_asset

Severidade:

HIGH

Condição:

Hostname não cadastrado.

Ação:

Gerar alerta.

---

# Regra 12

Máquina Offline

Evento:

machine_offline

Severidade:

LOW

Condição:

Sem check-in por mais de 10 minutos.

Ação:

Registrar ocorrência.

---

# Futuras Regras

* Wazuh Integration
* OpenVAS Integration
* IOC Detection
* Threat Hunting
* MITRE ATT&CK Mapping
* Vulnerability Correlation
* Active Directory Monitoring
* Microsoft 365 Monitoring

---

# Status de Implementacao - EPIC 6

Regras implementadas:

```text
failed_login
new_admin_user
firewall_disabled
defender_disabled
rdp_enabled
usb_detected
remote_access_tool_detected
unauthorized_remote_access_tool
unauthorized_vpn_tool
torrent_software_detected
```

Regras definidas, mas ainda nao implementadas no EPIC 6:

```text
unknown_asset
machine_offline
```

Comportamento atual:

* `firewall_disabled`: gerado quando `security.firewall_enabled` vem `false`; severidade `high`; gera alerta aberto.
* `defender_disabled`: gerado quando `security.defender_enabled` vem `false`; severidade `high`; gera alerta aberto.
* `rdp_enabled`: gerado quando `security.rdp_enabled` vem `true`; gera alerta `medium` quando a maquina nao estiver autorizada em ASSET_POLICY.md.
* `usb_detected`: gerado para cada dispositivo USB reportado; severidade `low`; nao gera alerta.
* `new_admin_user`: gerado quando surge administrador local novo apos o baseline inicial; severidade `high`; gera alerta aberto.
* `failed_login`: gerado quando `failed_logins_last_hour` for maior que 5; severidade `medium`; gera alerta aberto.
* `remote_access_tool_detected`: gerado para RustDesk; severidade `low`; nao gera alerta.
* `unauthorized_remote_access_tool`: gerado para AnyDesk, TeamViewer e UltraViewer; severidade `medium`; gera alerta aberto.
* `unauthorized_vpn_tool`: gerado para Hamachi, ZeroTier, Radmin VPN e Tailscale; severidade `high`; gera alerta aberto.
* `torrent_software_detected`: gerado para uTorrent, BitTorrent e qBittorrent; severidade `high`; gera alerta aberto.
* Alertas abertos nao sao duplicados para a mesma maquina e mesmo tipo.
* Eventos continuam sendo registrados a cada check-in em estado de risco.
