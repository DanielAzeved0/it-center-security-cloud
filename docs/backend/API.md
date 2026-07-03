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
```

`POST /api/v1/agent/checkin` continua usando `X-Agent-Api-Key`, separado do login humano.

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
  "security": {
    "firewall_enabled": true,
    "defender_enabled": true,
    "rdp_enabled": false,
    "local_admins": [
      "Administrator",
      "Daniel"
    ],
    "usb_devices": [],
    "failed_logins_last_hour": 0
  }
}
```

Efeitos SOC atuais:

```text
security.firewall_enabled = false -> security_event firewall_disabled + alerta high
security.defender_enabled = false -> security_event defender_disabled + alerta high
security.rdp_enabled = true -> security_event rdp_enabled; alerta medium se a maquina nao estiver autorizada em ASSET_POLICY.md
security.local_admins com novo admin apos baseline -> security_event new_admin_user + alerta high
security.usb_devices preenchido -> security_event usb_detected low
security.failed_logins_last_hour > 5 -> security_event failed_login + alerta medium
installed_programs com RustDesk -> security_event remote_access_tool_detected low
installed_programs com AnyDesk, TeamViewer ou UltraViewer -> security_event unauthorized_remote_access_tool + alerta medium
installed_programs com Hamachi, ZeroTier, Radmin VPN ou Tailscale -> security_event unauthorized_vpn_tool + alerta high
installed_programs com uTorrent, BitTorrent ou qBittorrent -> security_event torrent_software_detected + alerta high
```

Alertas abertos nao sao duplicados para a mesma maquina e mesmo tipo. Novos eventos continuam sendo registrados a cada check-in que mantiver o estado de risco.

Resposta:

```json
{
  "status": "success",
  "message": "Check-in received",
  "machine_id": 1
}
```

Efeitos de persistência:

```text
Cria ou atualiza a máquina em machines.
Registra uma nova linha em metrics.
Substitui o snapshot atual de installed_programs da máquina.
Cria agent_configs padrão para a máquina quando ainda não existir.
Atualiza last_seen e status online da máquina.
```

Erros esperados:

```json
{
  "detail": "Invalid or missing agent API key"
}
```

Payload invalido retorna `422 Unprocessable Entity` com a lista de campos invalidados pelo FastAPI/Pydantic.

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

Login bem-sucedido, falha de login e logout registram `audit_logs`.

O primeiro usuario `admin` deve ser criado por `backend/create_admin.py`, conforme `docs/security/AUTH.md`.

## Sessao Atual

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
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
    "status": "online",
    "last_seen": "2026-06-24T20:00:00"
  }
]
```

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
  "operating_system": "Windows 11 Pro",
  "os_version": "23H2",
  "status": "online",
  "last_seen": "2026-06-24T20:00:00"
}
```

---

# Metrics

## Métricas de uma Máquina

Retorna as últimas métricas de uma máquina.

```http
GET /api/v1/machines/{machine_id}/metrics
```

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
GET /api/v1/security-events
```

Filtros futuros:

```text
machine_id
event_type
severity
start_date
end_date
```

Observacao: o dashboard ja possui filtros locais por severidade, tipo e maquina usando os dados carregados. Esta secao se refere a filtros futuros na propria API, por query string.

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
GET /api/v1/alerts
```

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

Resposta:

```json
{
  "status": "success",
  "message": "Alert resolved"
}
```

---

# Regras Iniciais da API

## Segurança

No MVP inicial, endpoints administrativos podem funcionar sem login apenas em ambiente local/laboratório.

O endpoint de check-in do agente deverá exigir API Key desde a primeira implementação.

Header oficial:

```text
X-Agent-Api-Key
```

Antes de expor na internet, será obrigatório implementar:

```text
Autenticação no dashboard
HTTPS
Rate limit básico
Logs de auditoria
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
uTorrent
BitTorrent
qBittorrent
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
