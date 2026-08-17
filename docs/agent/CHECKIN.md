# CHECKIN.md

# IT Center Security Cloud - Agente Windows

## Objetivo

O agente Windows é responsável por coletar informações da máquina local e enviá-las para a API central do IT Center Security Cloud.

O agente deve ser:

* Leve
* Seguro
* Simples
* Autônomo
* Compatível com Windows 10 e Windows 11

---

# Responsabilidades

O agente deve:

* Coletar informações da máquina
* Coletar métricas
* Coletar eventos de segurança
* Enviar dados para a API
* Operar mesmo sem conexão temporária

---

# Dados Coletados

## Inventário

* Hostname (normalizado para maiúsculas antes do envio)
* Usuário logado
* Endereço IP
* MAC Address
* Número de Série (service tag, quando disponível)
* Sistema Operacional
* Versão do Windows
* CPU
* Memória RAM
* Disco

---

## Monitoramento

* Uso de CPU
* Uso de RAM
* Uso de Disco
* Uptime

---

## Segurança

* Firewall habilitado
* Defender habilitado
* RDP habilitado
* Usuários administradores locais
* Dispositivos USB
* Softwares instalados

---

# Dados Proibidos

O agente nunca deverá coletar:

* Senhas
* Cookies
* Histórico de navegação
* Conteúdo de documentos
* Arquivos pessoais
* E-mails

---

# Frequência de Coleta

Todo o payload (hostname, métricas, inventário e segurança) é coletado e enviado junto, numa única execução da Tarefa Agendada, no intervalo configurado em `checkin_interval_minutes` (padrão 5 minutos).

Não há throttling diferenciado por tipo de dado hoje: o código atual (`agent-windows/itcenter-agent.ps1`) não implementa frequências separadas para métricas, inventário e segurança. Os campos `collect_inventory`, `collect_metrics` e `collect_security` do `config.json` são aceitos e validados, mas atualmente não têm efeito sobre a coleta — servem apenas como reserva para uma futura implementação de coleta seletiva.

---

# Estrutura

Ver estrutura completa de arquivos em `agent-windows/README.md`.

---

# Fluxo

Coletar dados
↓
Gerar JSON
↓
Enviar API
↓
Receber resposta
↓
Registrar log

---

# Estado Atual da Implementação

O agente PowerShell ja possui coleta local, geracao de payload, envio autenticado para a API, cache offline, reenvio de pendencias e retry inteligente para falhas temporarias.

## Coletas implementadas

```text
Hostname
Usuário em execução
IPv4 local
Sistema operacional
Programas instalados
Uso de CPU
Uso de RAM
Uso de disco
Uptime em segundos
JSON de check-in
```

## JSON atual

O JSON gerado deve seguir o contrato do endpoint:

```text
POST /api/v1/agent/checkin
```

Campos gerados pelo agente hoje (`New-AgentCheckinPayload` em `agent-windows/itcenter-agent.ps1`):

```text
hostname
username
ip_address
mac_address
serial_number
operating_system
os_version
cpu_usage
ram_usage
disk_usage
uptime_seconds
installed_programs
security
```

Campo suportado pelo contrato da API mas **não enviado pelo agente atual**:

```text
processes  (opcional, backend/app/schemas/agent.py)
```

`agent_secret` (EPIC 28-A, ADR-036) já é enviado pelo agente: `New-AgentCheckinPayload` inclui `$script:AgentRuntimeConfig.agent_secret` (ausente/`null` até o primeiro check-in adotar um segredo) em todo payload, e `Start-ItCenterAgent` persiste de volta em `config.json` (via `Update-AgentConfigSecret`, que reescreve o arquivo em vez de recriá-lo, preservando a ACL restrita do ADR-025) o `agent_secret` devolvido pelo backend sempre que a resposta trouxer um valor não vazio. Falha ao persistir é registrada como `WARN` no log, sem interromper o check-in.

Observações:

* `hostname` é normalizado para maiúsculas (`ToUpperInvariant()`) antes do envio — relevante para comparar com a allowlist de hostnames em `docs/security/ASSET_POLICY.md`, que deve considerar o mesmo padrão.
* `mac_address` é obtido da mesma interface de rede escolhida para `ip_address` (mesma logica de fallback em cascata: `Get-NetIPAddress`+`Get-NetAdapter` -> `Win32_NetworkAdapterConfiguration` -> resolucao DNS, sem MAC neste ultimo nivel). Normalizado para o formato `AA:BB:CC:DD:EE:FF`. Pode ser `null` se nenhuma interface valida for encontrada.
* `serial_number` (EPIC 27) vem de `Get-CimInstance Win32_BIOS` (`SerialNumber`), com fallback para `Get-CimInstance Win32_ComputerSystemProduct` (`IdentifyingNumber`) quando o primeiro vier vazio ou for um placeholder conhecido (`System Serial Number`, `To Be Filled By O.E.M.`, `None`, `Not Specified`, `Default string`, `0`). Validado em 2026-08-14 contra hardware fisico real (Dell Inspiron 15 3530): os dois metodos retornaram o mesmo serial (`5M56TH4`). **Nao validado contra uma maquina virtual nesta sessao** (nenhuma VM disponivel para teste) — se o ambiente real apresentar um placeholder de VM fora da lista acima, o campo simplesmente fica `null` (nunca bloqueia o check-in); revisar a lista de placeholders assim que houver validacao real em VM. Pode ser `null` se a leitura falhar ou se ambos os metodos so retornarem placeholders.
* `processes` já é usado ativamente pelo backend para detecção SOC de ferramentas dual-use/malware em execução (ex.: `LockBit.exe`, `anydesk.exe`), mas o agente PowerShell não coleta lista de processos em execução. Se omitido, o backend trata como lista vazia.
* `installed_programs` agora é preenchido com o snapshot local dos programas instalados.
* O bloco `security` usa coletas reais do EPIC 6 para Firewall, Defender, RDP, administradores locais, USB e falhas de login.
* O agente já envia o check-in para `POST /api/v1/agent/checkin`.
* O JSON do check-in é enviado como bytes UTF-8 para suportar nomes de programas com acentos e caracteres especiais.
* Se a API falhar temporariamente, o agente aplica retry com atraso progressivo antes de salvar o JSON em `agent-windows/cache`.
* Falhas temporarias incluem timeout, erro de rede, HTTP 408, HTTP 429 e respostas 5xx.
* Falhas permanentes como HTTP 400, 401, 403 e 422 nao recebem retry excessivo.
* No próximo ciclo, o agente tenta reenviar check-ins pendentes antes de enviar a coleta atual.
* Um arquivo de cache corrompido (JSON invalido) e movido para `cache/quarantine/` em vez de travar o reenvio dos arquivos mais novos (EPIC 16).
* Arquivos de cache (incluindo `cache/quarantine/`) com mais de `cache_retention_days` (padrao 30 dias) sao removidos automaticamente antes de cada tentativa de reenvio (EPIC 16).
* O agente já registra as coletas em `agent-windows/logs/itcenter-agent.log`.
* O log e rotacionado por tamanho: ao atingir `log_max_size_kb` (padrao 5120 KB), o arquivo atual vira `.1` e os backups anteriores deslocam até `log_max_backups` (padrao 3) antes de descarte (EPIC 16).
* Em instalacao Windows, logs e cache usam os caminhos configurados em `config.json`.
* `server_url` pode apontar para a raiz do dominio publicado ou para a base local `/api/v1`.
* `config.json` tem a ACL restrita a `SYSTEM`/`Administrators` pelo instalador, protegendo o `agent_api_key` em texto puro contra leitura por usuarios comuns (EPIC 16).
* Falha de configuracao/inicializacao (`Start-ItCenterAgent`) e capturada no nivel mais alto e registrada com `Level = "ERROR"` antes de propagar o erro (EPIC 16).
* `agent_secret` (EPIC 28-A, ADR-036) fica ausente/`null` em `config.json` ate o primeiro check-in adotar um segredo; a partir dai o agente reenvia o mesmo valor em todo check-in seguinte.

## Testes atuais

Os testes do agente ficam em:

```text
agent-windows/tests/run-agent-tests.ps1
```

Eles validam:

```text
CPU entre 0 e 100
RAM entre 0 e 100
Disco entre 0 e 100
Payload com campos obrigatórios
JSON válido e parseável
Requisicao POST com header X-Agent-Api-Key
Body JSON enviado para /api/v1/agent/checkin
Cache offline em arquivo JSON
Reenvio de check-ins pendentes
Coletas de seguranca do EPIC 6
Config nova com agent_api_key e checkin_interval_minutes
Compatibilidade com config legada api_key e interval_minutes
Server URL raiz expandida para /api/v1/agent/checkin
Retry em falhas temporarias
Falha permanente sem retry excessivo
Logs de retry sem valor de API key
Rotacao de log por tamanho (log_max_size_kb, log_max_backups)
Quarentena de arquivo de cache corrompido sem bloquear reenvio dos demais
Retencao/expiracao de arquivos de cache por idade (cache_retention_days)
CPU via Get-Counter com fallback para Win32_Processor.LoadPercentage
Inventario de apps UWP/Store via Get-AppxPackage combinado ao registro
Deteccao de USB alem de armazenamento via Win32_PnPEntity
Falha de configuracao/inicializacao logada como ERROR em Start-ItCenterAgent
Preservacao/adocao de agent_secret em config.json (ADR-036)
Envio de agent_secret no payload de check-in (ADR-036)
```

---

# Cache Offline

Caso a API esteja indisponível:

* Salvar dados localmente
* Reenviar posteriormente

---

# Critério de Sucesso do Contrato Básico

O contrato basico do agente e considerado atendido quando:

* Conseguir coletar dados
* Gerar JSON válido
* Enviar para API
* Operar offline temporariamente

Esses pontos ja estao implementados e cobertos pelos testes do agente. Melhorias como assinatura de payloads e empacotamento independente ficam como evolucao futura sem plano formal ainda; atualizacao automatica ja tem plano formal registrado em ADR-032/EPIC 22 (`docs/development/DECISIONS.md`, `docs/development/TASKS.md`), implementacao ainda pendente.

---

# EPIC 6 - Coletas de Seguranca Implementadas

Coletas implementadas:

```text
Firewall habilitado
Windows Defender habilitado
RDP habilitado
Administradores locais
Dispositivos USB de armazenamento
Falhas de login na ultima hora
```

Campos enviados no bloco `security`:

```text
firewall_enabled
defender_enabled
rdp_enabled
local_admins
usb_devices
failed_logins_last_hour
```

Estado atual:

* `firewall_enabled` e coletado por `Get-NetFirewallProfile`.
* `defender_enabled` e coletado por `Get-MpComputerStatus`.
* `rdp_enabled` e coletado no registro `HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server`.
* `local_admins` e coletado pelo grupo local de administradores via SID `S-1-5-32-544`.
* `usb_devices` coleta metadados tecnicos de discos USB (`type: "storage"`) e de outros dispositivos USB via `Win32_PnPEntity` (`type` = classe PnP, ex.: `HIDClass`), sem ler conteudo de arquivos (EPIC 16).
* `failed_logins_last_hour` conta eventos 4625 no log Security da ultima hora; se o log nao estiver acessivel, retorna 0.
* Os testes do agente validam as coletas do EPIC 6.

---

# EPIC 16 - Hardening do Agente Windows

Lacunas de robustez corrigidas (ver ADR-025 e `docs/development/TASKS.md`):

```text
ACL de config.json restrita a SYSTEM/Administrators (instalador)
Quarentena de cache corrompido em cache/quarantine/
Retencao por idade em cache/ (cache_retention_days)
Rotacao de logs/itcenter-agent.log por tamanho (log_max_size_kb, log_max_backups)
CPU via Get-Counter '\Processor(_Total)\% Processor Time' com fallback WMI
Inventario incluindo apps UWP/Store (Get-AppxPackage -AllUsers)
Deteccao de USB alem de armazenamento (Win32_PnPEntity)
try/catch no nivel mais alto de Start-ItCenterAgent com log ERROR explicito
Scripts assinados com certificado Authenticode self-signed; Tarefa Agendada com ExecutionPolicy AllSigned (ADR-031, `docs/development/DECISIONS.md`)
```

EPIC 16 concluida.
