# API.md

# IT Center Security Cloud - API Oficial

## Objetivo

Definir os endpoints iniciais da API do IT Center Security Cloud.

A API será responsável por:

* Receber dados dos agentes Windows.
* Salvar informações no PostgreSQL.
* Listar máquinas cadastradas.
* Exibir métricas.
* Exibir eventos de segurança.
* Exibir alertas.

---

# Tecnologia

Backend:

```text
Python + FastAPI
```

Base URL:

```text
/api/v1
```

Autenticacao administrativa:

```http
Authorization: Bearer <access_token>
```

Rotas administrativas exigem Bearer token. As excecoes sao:

```text
GET /api/v1/health
POST /api/v1/auth/login
POST /api/v1/agent/checkin
GET /api/v1/agent/manifest
GET /api/v1/agent/download
```

`POST /api/v1/agent/checkin`, `GET /api/v1/agent/manifest` e `GET /api/v1/agent/download` continuam usando `X-Agent-Api-Key`, separado do login humano (EPIC 22, ADR-032).

---

# Endpoints MVP

## Health Check

Verifica se a API está funcionando.

```http
GET /api/v1/health
```

Resposta:

```json
{
  "status": "healthy",
  "service": "it-center-security-cloud"
}
```

---

# Agent

## Check-in do Agente

Recebe os dados enviados pelo agente PowerShell.

```http
POST /api/v1/agent/checkin
```

Autenticação obrigatória:

```http
X-Agent-Api-Key: <agent_api_key>
```

Exemplo de envio:

```json
{
  "hostname": "PC-FINANCEIRO-01",
  "username": "daniel",
  "ip_address": "192.168.15.25",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "serial_number": "5M56TH4",
  "operating_system": "Windows 11 Pro",
  "os_version": "23H2",
  "cpu_usage": 22.5,
  "ram_usage": 61.2,
  "disk_usage": 74.8,
  "uptime_seconds": 86400,
  "installed_programs": [
    {
      "name": "Google Chrome",
      "version": "126.0",
      "publisher": "Google"
    }
  ],
  "processes": [
    "chrome.exe",
    "explorer.exe"
  ],
  "security": {
    "firewall_enabled": true,
    "defender_enabled": true,
    "rdp_enabled": false,
    "local_admins": [
      "Administrator",
      "Daniel"
    ],
    "usb_devices": [
      {
        "name": "Kingston DataTraveler 3.0"
      }
    ],
    "failed_logins_last_hour": 0
  },
  "agent_secret": "opcional-string-ate-128-caracteres",
  "agent_version": "1.0.0"
}
```

`agent_version` (EPIC 22, ADR-032) é opcional e informa a versão do próprio `itcenter-agent.ps1` em execução (`$script:AgentVersion`), usada só para observabilidade e pela auto-atualização — nenhuma regra SOC depende dela. Persistida em `machines.agent_version` a cada check-in, mesmo padrão de sobrescrita de `mac_address`/`serial_number` (ausência sobrescreve com `null`).

`agent_secret` (EPIC 28-A, ADR-036) é opcional e implementa trust-on-first-use por máquina, além da `AGENT_API_KEY` global: no primeiro check-in de um hostname novo (ou de um hostname já cadastrado sem segredo ainda adotado), o backend ignora o valor enviado, gera um segredo aleatório de 256 bits e o devolve em texto puro só na resposta desse check-in — a partir daí, todo check-in seguinte para aquele hostname precisa enviar esse mesmo valor em `agent_secret` (comparado só pelo hash, `sha256`, nunca guardado em texto puro). Um check-in sem o segredo certo é rejeitado com `401` e não altera nenhum dado da máquina.

`usb_devices` é `list[dict]` sem schema fixo no Pydantic (`list[dict[str, Any]]`), mas a API só lê a chave `name` de cada item (`device.get("name")`, com fallback para `"USB device"` quando ausente) para compor a descrição do `security_event` `usb_detected`. Outras chaves enviadas pelo agente são aceitas mas ignoradas.

`processes` é opcional e traz os nomes dos processos em execução no momento da coleta. Eles passam pelas mesmas listas de ferramentas remotas autorizadas/não autorizadas, ferramentas dual-use e indicadores de malware/ransomware usadas em `installed_programs` — ver `malware_or_ransomware_indicator` e `suspicious_tool_detected` abaixo. As listas de VPN não autorizada (`unauthorized_vpn_tool`) e torrent (`torrent_software_detected`) só são avaliadas para `installed_programs`; `processes` não passa por essas duas checagens.

Efeitos SOC atuais:

```text
hostname fora de KNOWN_ASSET_HOSTNAMES (ASSET_POLICY.md) -> security_event unknown_asset + alerta high; verificado incondicionalmente em todo check-in, nao depende de nenhum campo especifico de security
security.firewall_enabled = false -> security_event firewall_disabled + alerta high
security.defender_enabled = false -> security_event defender_disabled + alerta high
security.rdp_enabled = true -> security_event rdp_enabled; alerta medium se a maquina nao estiver autorizada em ASSET_POLICY.md
security.local_admins com novo admin apos baseline -> security_event new_admin_user + alerta high
security.usb_devices preenchido -> security_event usb_detected low
security.failed_logins_last_hour > 5 -> security_event failed_login + alerta medium
installed_programs ou processes com RustDesk -> security_event remote_access_tool_detected low
installed_programs ou processes com AnyDesk, TeamViewer ou UltraViewer -> security_event unauthorized_remote_access_tool + alerta medium
installed_programs com Hamachi, ZeroTier, Radmin VPN ou Tailscale -> security_event unauthorized_vpn_tool + alerta high
installed_programs com uTorrent, BitTorrent ou qBittorrent -> security_event torrent_software_detected + alerta high
installed_programs ou processes com Mimikatz, WannaCry, WCry, LockBit, BlackCat, ALPHV, Conti, Ryuk, REvil ou DarkSide -> security_event malware_or_ransomware_indicator + alerta high
installed_programs ou processes com Advanced IP Scanner, Angry IP Scanner, Nmap, Masscan, PsExec, PAExec, Metasploit, Cobalt Strike, Process Hacker, Netcat, Rclone, MegaSync ou Tor Browser -> security_event suspicious_tool_detected + alerta medium
agent_secret ausente ou incorreto para um hostname que ja adotou um segredo (EPIC 28-A, ADR-036) -> rejeita o check-in (401) + security_event machine_identity_mismatch + alerta high; nao sobrescreve nenhum dado da maquina
```

Alertas abertos nao sao duplicados para a mesma maquina e mesmo tipo — garantido por indice unico parcial em `alerts(machine_id, alert_type) WHERE status IN ('open','investigating')` (migration `010_alerts_open_unique_index.sql`, EPIC 30): `create_open_alert_once` virou um unico `INSERT ... ON CONFLICT ... DO NOTHING`, atomico, sem a race condition real que existia entre o `SELECT` e o `INSERT` de chamadas separadas sob retry do agente. Novos eventos continuam sendo registrados a cada check-in que mantiver o estado de risco. Duas entradas de `installed_programs` que casam com a mesma ferramenta de VPN nao autorizada ou torrent no mesmo check-in geram só 1 evento/alerta (EPIC 30) — mesmo padrão de deduplicação já usado para ferramentas remotas não autorizadas, dual-use e malware/ransomware.

Resposta:

```json
{
  "status": "success",
  "message": "Check-in received",
  "machine_id": 1,
  "agent_secret": "segredo-em-texto-puro-so-nesta-resposta"
}
```

`agent_secret` na resposta só vem preenchido quando o backend emite ou adota um segredo novo nesse check-in (primeiro check-in do hostname, ou hostname já cadastrado que ainda não tinha segredo); em qualquer outro check-in vem `null` (EPIC 28-A, ADR-036).

Efeitos de persistência:

```text
Cria ou atualiza a máquina em machines.
Registra uma nova linha em metrics.
Substitui o snapshot atual de installed_programs da máquina.
Cria agent_configs padrão para a máquina quando ainda não existir.
Sincroniza machine_local_admins com o baseline recebido em security.local_admins, registrando novos administradores.
Atualiza last_seen e status online da máquina.
Emite ou adota agent_secret_hash (EPIC 28-A, ADR-036) quando aplicavel.
Persiste agent_version quando enviado (EPIC 22, ADR-032).
```

Erros esperados:

```json
{
  "detail": "Invalid or missing agent API key"
}
```

```json
{
  "detail": "Invalid or missing machine identity secret"
}
```

O segundo erro (`401 Unauthorized`) ocorre quando o hostname já adotou um `agent_secret` e o check-in atual não envia o valor correto (EPIC 28-A, ADR-036) — nesse caso nenhum dado da máquina é sobrescrito e um `security_event`/`alert` `machine_identity_mismatch` é registrado.

Payload invalido retorna `422 Unprocessable Entity` com a lista de campos invalidados pelo FastAPI/Pydantic. `ip_address`, quando enviado (não `null`/vazio), precisa ser um IPv4 ou IPv6 válido (`ipaddress.ip_address()`, EPIC 30) — antes um valor inválido só era pego na hora do `INSERT` na coluna `INET`, subindo como `500 Internal Server Error` genérico em vez do `422` de validação esperado.

Se `AGENT_API_KEY` nao estiver configurada no servidor, a API retorna `500 Internal Server Error` com `{"detail": "Agent API key is not configured"}`, antes mesmo de validar o header enviado pelo agente.

---

## Manifest do Agente (EPIC 22, ADR-032)

Consultado por `agent-windows/itcenter-agent-updater.ps1` para decidir se atualiza a instalação local.

```http
GET /api/v1/agent/manifest
GET /api/v1/agent/manifest?hostname=PC-FINANCEIRO-01
```

Autenticação obrigatória: `X-Agent-Api-Key`, mesmo header/valor do check-in.

Resposta:

```json
{
  "version": "1.1.0",
  "sha256": "3f7b...",
  "target_agent_version": null
}
```

`version`/`sha256` descrevem a versão de `itcenter-agent.ps1` atualmente publicada por este backend (extraída via regex de `$script:AgentVersion` do arquivo copiado para dentro da imagem do backend em build-time — ver `docs/backend/DATABASE.md`/ADR-032 sobre onde esse arquivo vive). `target_agent_version` só vem preenchido quando o parâmetro de query `hostname` bate com uma máquina cadastrada que tenha `machines.target_agent_version` definido (trava de "não atualizar" — ver seção "Coluna target_agent_version" em `DATABASE.md`); ausência do parâmetro, ou hostname sem correspondência, devolve `null`. Sem RBAC de usuário humano aqui — é a mesma autenticação de classe do agente, não identidade individual (ADR-036 continua sendo só sobre `/agent/checkin`).

Erros: `401` (API key ausente/inválida, mesmo formato do check-in), `500` quando o backend não tem nenhum release do agente configurado (`AGENT_RELEASE_PATH` aponta para um arquivo inexistente ou sem `$script:AgentVersion`).

## Download do Agente (EPIC 22, ADR-032)

```http
GET /api/v1/agent/download
```

Autenticação obrigatória: `X-Agent-Api-Key`. Resposta `200` com `Content-Type: application/octet-stream` e o corpo sendo os bytes exatos do script cujo hash é o mesmo devolvido por `/agent/manifest` — o updater valida assinatura Authenticode (certificado do ADR-031) e o hash SHA-256 antes de substituir o script instalado, sem nenhum fallback de bypass (diferente do instalador, que tem `-SkipSignatureCheck` só para uso local/dev). Mesmos erros `401`/`500` do manifest.

---

# Auth

## Login Administrativo

Autentica usuario humano administrativo.

```http
POST /api/v1/auth/login
```

Exemplo de envio:

```json
{
  "email": "admin@example.com",
  "password": "senha"
}
```

Resposta:

```json
{
  "access_token": "token",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "name": "Admin User",
    "role": "admin"
  }
}
```

Erro quando o e-mail não existe, o usuário não está `active` ou a senha não confere:

```json
{
  "detail": "Invalid credentials"
}
```

Retornado com status `401 Unauthorized`. Nesse caso a API também registra `audit_logs` com `action = "auth.login_failed"` antes de responder.

Validação do payload (Pydantic, `LoginRequest`):

```text
email: string, min_length=3, max_length=255
password: string, min_length=1, max_length=1024
```

Payload fora desses limites (ou faltando campo obrigatório) retorna `422 Unprocessable Entity` com a lista de campos invalidados pelo FastAPI/Pydantic, antes mesmo de consultar o banco.

Login bem-sucedido, falha de login e logout registram `audit_logs`.

O primeiro usuario `admin` deve ser criado por `backend/create_admin.py`, conforme `docs/security/AUTH.md`.

## Sessao Atual

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

Resposta:

```json
{
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "name": "Admin User",
    "role": "admin"
  }
}
```

## Logout

```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

Resposta:

```json
{
  "status": "success",
  "message": "Logged out"
}
```

---

# Machines

## Listar Máquinas

Lista todas as máquinas cadastradas.

```http
GET /api/v1/machines
```

Resposta:

```json
[
  {
    "id": 1,
    "hostname": "PC-FINANCEIRO-01",
    "username": "daniel",
    "ip_address": "192.168.15.25",
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "serial_number": "5M56TH4",
    "status": "online",
    "last_seen": "2026-06-24T20:00:00",
    "rustdesk_id": "123456789",
    "agent_version": "1.0.0",
    "target_agent_version": null
  }
]
```

`rustdesk_id` é `null` quando a máquina ainda não teve o ID cadastrado (EPIC 19, ADR-027). `serial_number` é `null` quando o agente não conseguiu ler o número de série da máquina (EPIC 27) — nunca bloqueia o check-in. `agent_version` é `null` até o primeiro check-in que a informe (EPIC 22, ADR-032); `target_agent_version` é `null` a menos que um operador o defina manualmente via SQL (sem endpoint de escrita nesta EPIC).

Origem dos dados:

```text
Tabela machines no PostgreSQL.
```

---

## Detalhar Máquina

Retorna informações completas de uma máquina.

```http
GET /api/v1/machines/{machine_id}
```

Resposta:

```json
{
  "id": 1,
  "hostname": "PC-FINANCEIRO-01",
  "username": "daniel",
  "ip_address": "192.168.15.25",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "serial_number": "5M56TH4",
  "operating_system": "Windows 11 Pro",
  "os_version": "23H2",
  "status": "online",
  "last_seen": "2026-06-24T20:00:00",
  "rustdesk_id": "123456789",
  "agent_version": "1.0.0",
  "target_agent_version": null
}
```

`rustdesk_id` é `null` quando ainda não cadastrado (EPIC 19, ADR-027). `agent_version`/`target_agent_version`: ver nota na listagem de máquinas acima (EPIC 22, ADR-032).

Quando a máquina não existir, a API retorna `404 Machine not found`.

---

## Cadastrar RustDesk ID

Cadastra ou limpa o ID do RustDesk de uma máquina.

```http
PATCH /api/v1/machines/{machine_id}/rustdesk
```

Requer papel `admin` ou `analyst` (`viewer` recebe `403`).

Exemplo de envio:

```json
{
  "rustdesk_id": "123456789"
}
```

Envie `"rustdesk_id": null` para limpar o cadastro.

Resposta:

```json
{
  "status": "success",
  "message": "Rustdesk ID updated"
}
```

Quando a máquina não existir, a API retorna `404 Machine not found`.

Registra `audit_logs` com `action = "machine.rustdesk_update"`.

---

# Metrics

## Métricas de uma Máquina

Retorna as últimas métricas de uma máquina.

```http
GET /api/v1/machines/{machine_id}/metrics?limit=100&offset=0
```

Parâmetros de query (EPIC 30, opcionais):

```text
limit: int, padrão 100, mínimo 1, máximo 500
offset: int, padrão 0, mínimo 0
```

Valores fora do intervalo retornam `422 Unprocessable Entity`. Resultado ordenado por `created_at DESC` (mais recente primeiro) — `limit`/`offset` paginam a partir daí.

Resposta:

```json
[
  {
    "cpu_usage": 22.5,
    "ram_usage": 61.2,
    "disk_usage": 74.8,
    "uptime_seconds": 86400,
    "created_at": "2026-06-24T20:00:00"
  }
]
```

Quando a máquina não existir, a API retorna `404 Machine not found`.

---

# Installed Programs

## Programas Instalados

Retorna programas instalados em uma máquina.

```http
GET /api/v1/machines/{machine_id}/programs
```

Resposta:

```json
[
  {
    "name": "Google Chrome",
    "version": "126.0",
    "publisher": "Google"
  }
]
```

Quando a máquina não existir, a API retorna `404 Machine not found`.

---

# Local Admins

## Administradores Locais

Retorna o baseline conhecido de administradores locais de uma máquina.

```http
GET /api/v1/machines/{machine_id}/admins
```

Resposta:

```json
[
  {
    "admin_name": "Administrator",
    "first_seen_at": "2026-06-24T20:00:00",
    "last_seen_at": "2026-06-24T20:05:00"
  }
]
```

Origem dos dados:

```text
Tabela machine_local_admins no PostgreSQL.
```

Quando a máquina não existir, a API retorna `404 Machine not found`.

---

# Security Events

## Listar Eventos de Segurança

Lista eventos de segurança.

```http
GET /api/v1/security-events?machine_id=1&limit=100&offset=0
```

Parâmetros de query (EPIC 30, todos opcionais):

```text
machine_id: int, filtra por máquina
limit: int, padrão 100, mínimo 1, máximo 500
offset: int, padrão 0, mínimo 0
```

`limit` fora do intervalo 1-500 retorna `422 Unprocessable Entity`. Resultado ordenado por `created_at DESC, id DESC`. `MachineDetailView` (dashboard) usa `machine_id` para buscar só os eventos da máquina em vez de carregar a lista inteira e filtrar no cliente (antes tech debt registrada na EPIC 26 — corrigida na EPIC 30 justamente para não esconder eventos de uma máquina quando o total do parque ultrapassar `limit`). `AlertsView`/`SecurityView` (listas administrativas completas) continuam sem UI de paginação — exibem só os `limit` registros mais recentes por padrão; extensão futura fica para uma spec própria caso o volume de produção cresça.

Filtros futuros ainda não implementados: `event_type`, `severity`, `start_date`, `end_date`.

Resposta:

```json
[
  {
    "id": 1,
    "machine_id": 1,
    "event_type": "unauthorized_remote_access_tool",
    "severity": "medium",
    "source": "agent",
    "description": "Ferramenta remota não autorizada detectada: AnyDesk",
    "created_at": "2026-06-24T20:00:00"
  }
]
```

Origem dos dados:

```text
Tabela security_events no PostgreSQL.
```

---

# Alerts

## Listar Alertas

Lista alertas gerados pelo sistema.

```http
GET /api/v1/alerts?machine_id=1&limit=100&offset=0
```

Parâmetros de query (EPIC 30, todos opcionais):

```text
machine_id: int, filtra por máquina
limit: int, padrão 100, mínimo 1, máximo 500
offset: int, padrão 0, mínimo 0
```

`limit` fora do intervalo 1-500 retorna `422 Unprocessable Entity`. Resultado ordenado por `created_at DESC, id DESC`. Mesma observação de `machine_id`/paginação de `GET /api/v1/security-events` acima se aplica aqui (uso em `MachineDetailView`, ausência de UI de paginação em `AlertsView`).

Resposta:

```json
[
  {
    "id": 1,
    "machine_id": 1,
    "alert_type": "unauthorized_remote_access_tool",
    "severity": "medium",
    "status": "open",
    "title": "Ferramenta remota não autorizada",
    "description": "AnyDesk foi encontrado na máquina PC-FINANCEIRO-01",
    "created_at": "2026-06-24T20:00:00"
  }
]
```

Origem dos dados:

```text
Tabela alerts no PostgreSQL.
```

---

## Resolver Alerta

Marca um alerta como resolvido.

```http
PATCH /api/v1/alerts/{alert_id}/resolve
```

Requer papel `admin` ou `analyst` (`viewer` recebe `403`).

Resposta:

```json
{
  "status": "success",
  "message": "Alert resolved"
}
```

Registra `audit_logs` com `action = "alert.resolve"`.

---

# Dashboard Executivo

## Resumo do Dashboard

Retorna um resumo agregado (máquinas online/offline, alertas abertos por severidade, eventos recentes), evitando que a tela executiva precise de múltiplas chamadas.

```http
GET /api/v1/dashboard/summary
```

Requer papel `admin`, `analyst` ou `viewer`.

Resposta:

```json
{
  "machines_total": 12,
  "machines_online": 9,
  "machines_offline": 3,
  "alerts_open_total": 4,
  "alerts_open_by_severity": {
    "low": 1,
    "medium": 2,
    "high": 1,
    "critical": 0
  },
  "recent_events": [
    {
      "id": 42,
      "machine_id": 3,
      "event_type": "usb_device_connected",
      "severity": "medium",
      "source": "agent",
      "description": "Dispositivo USB conectado",
      "created_at": "2026-08-11T12:00:00"
    }
  ]
}
```

`alerts_open_by_severity` conta alertas com status `open` ou `investigating`. `recent_events` traz os 10 eventos mais recentes (mesma origem de `GET /api/v1/security-events`).

Origem dos dados:

```text
Agregação de machines, alerts e security_events no PostgreSQL.
```

---

# Exportação de Relatórios PDF

Gerados com `reportlab` (Python puro, compatível com a imagem Alpine do backend — ver ADR-029). Ambos exigem papel `admin`, `analyst` ou `viewer`, respondem `Content-Type: application/pdf` e `Content-Disposition: attachment`.

## Relatório Executivo

```http
GET /api/v1/reports/executive.pdf
```

PDF com os mesmos indicadores de `GET /api/v1/dashboard/summary` (máquinas online/offline, alertas por severidade, eventos recentes).

## Relatório de Máquina

```http
GET /api/v1/machines/{machine_id}/report.pdf
```

PDF com o detalhe da máquina, últimas métricas, alertas, eventos de segurança, programas instalados e administradores locais — mesmos dados já expostos em `GET /api/v1/machines/{machine_id}` e endpoints relacionados. Alertas e eventos são filtrados por `machine_id` diretamente no SQL (`list_alerts(machine_id=...)`/`list_security_events(machine_id=...)`, EPIC 30) em vez de carregar a listagem inteira do parque e filtrar em Python.

Quando a máquina não existir, a API retorna `404 Machine not found`.

---

# Regras Iniciais da API

## Segurança

O endpoint de check-in do agente exige API Key desde a primeira implementação.

Header oficial:

```text
X-Agent-Api-Key
```

Estado atual (EPIC 12/13):

```text
Autenticação no dashboard: implementada (Bearer token HMAC SHA-256, ver docs/security/AUTH.md).
HTTPS: implementado (Nginx em produção).
Logs de auditoria: implementados (audit_logs — login, falha de login, logout, resolução de alerta, atualização do RustDesk ID via `machine.rustdesk_update`).
Rate limit implementado no check-in do agente (Nginx, `limit_req_zone ... zone=agent_checkins`, validado em produção); rate limit geral nas demais rotas ainda não implementado.
```

---

# Status Online/Offline

Regra inicial:

```text
Se last_seen for menor que 10 minutos:
    online

Se last_seen for maior que 10 minutos:
    offline
```

**Atenção — a transição para offline acontece dentro de uma leitura, não em um job de background.** `GET /api/v1/machines`, `GET /api/v1/machines/{machine_id}` e `GET /api/v1/dashboard/summary` chamam `mark_stale_machines_offline()` antes de responder. Essa função faz um `UPDATE` em `machines.status` para `offline` em qualquer máquina cujo `last_seen` esteja além de `OFFLINE_THRESHOLD_MINUTES` (10 minutos) e, para cada máquina que transicionar, insere um `security_events` do tipo `machine_offline`. Ou seja, consultar essas três rotas pode gravar dados como efeito colateral de uma requisição GET — não existe hoje um worker separado que marque máquinas como offline.

Os dois endpoints de exportação em PDF (EPIC 20) reaproveitam os mesmos services e têm o mesmo efeito colateral: `GET /api/v1/machines/{machine_id}/report.pdf` chama `get_registered_machine()` (mesmo caminho de `GET /api/v1/machines/{machine_id}`) e `GET /api/v1/reports/executive.pdf` chama `get_registered_dashboard_summary()` (mesmo caminho de `GET /api/v1/dashboard/summary`) — ou seja, baixar um relatório em PDF também pode gravar `machines.status`/`security_events` como efeito colateral, mesmo sendo uma exportação.

---

# Eventos Gerados Automaticamente

A API poderá gerar eventos quando detectar:

```text
Ferramenta monitorada instalada
Ferramenta remota não autorizada
VPN não autorizada
Torrent detectado
Firewall desativado
Defender desativado
RDP habilitado
Falhas excessivas de login
Novo administrador local
USB conectado
Hostname fora da allowlist de ativos conhecidos (unknown_asset)
Máquina sem check-in por mais de 10 minutos (machine_offline)
Indicador de malware ou ransomware (malware_or_ransomware_indicator)
Ferramenta sensível ou dual-use detectada (suspicious_tool_detected)
Identidade de máquina não confere no check-in (machine_identity_mismatch)
```

---

# Softwares Monitorados Iniciais

A classificação deve respeitar ASSET_POLICY.md antes de gerar alertas.

Ferramentas de acesso remoto autorizadas devem gerar evento informativo, não alerta automático.

```text
AnyDesk
TeamViewer
UltraViewer
RustDesk
Hamachi
ZeroTier
Radmin VPN
Tailscale
uTorrent
BitTorrent
qBittorrent
```

Ferramentas dual-use (evento `suspicious_tool_detected`, severidade medium, gera alerta):

```text
Advanced IP Scanner
Angry IP Scanner
Nmap
Masscan
PsExec
PAExec
Metasploit
Cobalt Strike
Process Hacker
Netcat
Rclone
MegaSync
Tor Browser
```

Indicadores de malware/ransomware (evento `malware_or_ransomware_indicator`, severidade high, gera alerta):

```text
Mimikatz
WannaCry
WCry
LockBit
BlackCat
ALPHV
Conti
Ryuk
REvil
DarkSide
```

---

# Critério de Conclusão do MVP da API

A API estará pronta para o MVP quando:

* GET /api/v1/health funcionar.
* POST /api/v1/agent/checkin receber dados com API Key válida.
* Dados forem salvos no PostgreSQL.
* GET /api/v1/machines listar máquinas.
* GET /api/v1/machines/{id} detalhar máquina.
* GET /api/v1/machines/{id}/metrics listar métricas da máquina.
* GET /api/v1/machines/{id}/programs listar programas da máquina.
* GET /api/v1/machines/{id}/admins listar administradores locais da máquina.
* GET /api/v1/security-events listar eventos.
* GET /api/v1/alerts listar alertas.
* PATCH /api/v1/alerts/{id}/resolve resolver alertas.
