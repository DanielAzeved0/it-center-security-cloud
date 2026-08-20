# ASSET_POLICY.md

# Política de Ativos

## Objetivo

Definir quais ativos, softwares e comportamentos são considerados autorizados dentro do ambiente monitorado pelo IT Center Security Cloud.

As regras SOC devem consultar este documento antes de gerar alertas.

---

# Ambientes

## Produção

Máquinas utilizadas pelos colaboradores.

## TI

Máquinas utilizadas para suporte, administração e manutenção.

## Servidores

Servidores físicos ou virtuais.

---

# Ativos Conhecidos

No MVP, a regra SOC `unknown_asset` usa uma allowlist simples de hostnames conhecidos.

Fonte oficial documental:

```text
ASSET_POLICY.md
```

Lista inicial de hostnames conhecidos:

```text
NOTE-DANIEL
PC-TI-01
PC-TI-02
PC-FINANCEIRO-01
```

Regra operacional:

```text
Se um check-in chegar com hostname fora desta lista, o backend registra unknown_asset e gera alerta high.
```

Normalização:

* Comparar hostnames em caixa alta.
* Ignorar espaços no início e no fim.

Limitação conhecida:

* A allowlist também existe no código do backend enquanto não houver tabela ou tela administrativa de ativos.
* Quando a governança evoluir, esta lista deverá migrar para banco de dados e administração pelo dashboard.

---

# Ferramentas de Acesso Remoto

## Autorizadas

* RustDesk

Justificativa:

Ferramenta utilizada pela equipe de TI para suporte remoto.

---

## Não Autorizadas

* AnyDesk
* TeamViewer
* UltraViewer

Motivo:

Não fazem parte do padrão atual da operação.

---

# Ferramentas Sensiveis e Indicadores de Malware

Esta secao define ferramentas que podem ser legitimas em administracao de TI, mas tambem podem ser abusadas em reconhecimento, movimentacao lateral, exfiltracao, persistencia ou operacoes de ransomware.

Esta deteccao e heuristica e nao substitui antivirus, EDR, analise de comportamento, YARA, Sigma ou threat intelligence externa.

## Ferramentas Dual-Use ou Sensiveis

Geram evento `suspicious_tool_detected`, severidade `medium`, com alerta aberto.

* Advanced IP Scanner
* Angry IP Scanner
* Nmap
* Masscan
* PsExec
* PAExec
* Metasploit
* Cobalt Strike
* Process Hacker
* Netcat
* nc.exe (alias de Netcat no código, entrada separada em `DUAL_USE_TOOLS`, `backend/app/services/agent.py`)
* Rclone
* MegaSync
* Tor Browser

## Indicadores Fortes de Malware ou Ransomware

Geram evento `malware_or_ransomware_indicator`, severidade `high`, com alerta aberto.

* Mimikatz
* WannaCry
* WCry
* LockBit
* BlackCat
* ALPHV
* Conti
* Ryuk
* REvil
* DarkSide

Regra operacional:

```text
RustDesk gera remote_access_tool_detected low sem alerta.
AnyDesk, TeamViewer e UltraViewer geram unauthorized_remote_access_tool medium com alerta.
Ferramentas dual-use geram suspicious_tool_detected medium com alerta.
Indicadores fortes de malware/ransomware geram malware_or_ransomware_indicator high com alerta.
```

Normalizacao:

* Comparar nomes sem diferenciar maiusculas e minusculas.
* Aceitar correspondencia por substring para nomes como TeamViewer Host, AnyDesk MSI, rustdesk.exe e lockbit.exe.
* Avaliar programas instalados e processos em execucao quando o payload do agente trouxer essas informacoes — inclui `unauthorized_vpn_tool` e `torrent_software_detected` (Regras 9 e 10, `docs/security/SOC_RULES.md`), corrigido em 2026-08-19 (EPIC 37): as duas passaram a avaliar tambem `processes`, nao so `installed_programs` (gap real identificado numa auditoria de documentacao no mesmo dia, corrigido na mesma sessao).

Limitacao conhecida:

* As listas tambem existem no codigo do backend enquanto nao houver tabela ou tela administrativa de politicas.
* Eventos indicam evidencia operacional para investigacao, nao confirmacao definitiva de comprometimento.

---

# VPNs

## Não Autorizadas

* Hamachi
* ZeroTier
* Radmin VPN
* Tailscale

Motivo:

Podem criar túneis não controlados para dentro da rede.

---

# Softwares Proibidos

## Torrent

* uTorrent
* BitTorrent
* qBittorrent

Motivo:

Risco jurídico e operacional.

---

# Acesso Remoto

## Máquinas Autorizadas

Categoria:

Equipe de TI

Exemplos:

* NOTE-DANIEL
* PC-TI-01
* PC-TI-02

Observação:

A lista real será mantida conforme o inventário crescer.

Relação com a seção RDP: esta é a lista geral de máquinas autorizadas a acesso remoto (perfil equipe de TI). O caso de uso específico de RDP habilitado é coberto pela allowlist de hostnames em `RDP > Hostnames Autorizados no MVP` (abaixo) e pela Regra 5 de `SOC_RULES.md` — no MVP, é a mesma lista de hostnames aplicada a esse caso de uso especifico.

---

# RDP

## Permitido

* Servidores
* Máquinas da equipe de TI

## Hostnames Autorizados no MVP

```text
NOTE-DANIEL
PC-TI-01
PC-TI-02
```

Esta lista corresponde, no MVP, à mesma allowlist de `Acesso Remoto > Máquinas Autorizadas` (acima), aqui aplicada especificamente à regra operacional de RDP (Regra 5 de `SOC_RULES.md`).

Regra operacional:

```text
RDP habilitado em hostname autorizado gera evento informativo low e nao gera alerta.
RDP habilitado fora desta lista gera evento medium e alerta aberto.
```

Normalização:

* Comparar hostnames em caixa alta.
* Ignorar espaços no início e no fim.

Limitação conhecida:

* A allowlist de RDP também existe no código do backend enquanto não houver tabela ou tela administrativa de politicas.

## Não Permitido

* Estações comuns de usuários

---

# USB

## Permitido

* Teclados
* Mouses
* Headsets

## Monitorado

* Pendrives
* HDs externos
* SSDs externos
* Smartphones

---

# Antivírus

Obrigatório:

* Microsoft Defender

---

# Firewall

Obrigatório:

* Windows Firewall habilitado

---

# Softwares Obrigatórios

* Microsoft 365
* OneDrive
* Navegador Corporativo

Lista será expandida futuramente.

---

# Responsáveis

Equipe de TI

Responsável atual:

Daniel da Silva Azevedo

---

# Processo de Atualização

Sempre que uma nova ferramenta for aprovada ou removida da operação, este documento deverá ser atualizado antes da alteração das regras SOC.

ASSET_POLICY.md é a fonte oficial para validação de softwares e comportamentos autorizados.
