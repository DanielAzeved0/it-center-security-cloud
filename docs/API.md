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

Resposta:

```json
{
  "status": "success",
  "message": "Check-in received",
  "machine_id": 1
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

Resposta:

```json
[
  {
    "id": 1,
    "machine_id": 1,
    "event_type": "suspicious_software",
    "severity": "medium",
    "source": "agent",
    "description": "Software suspeito detectado: AnyDesk",
    "created_at": "2026-06-24T20:00:00"
  }
]
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
    "alert_type": "suspicious_software",
    "severity": "medium",
    "status": "open",
    "title": "Software suspeito detectado",
    "description": "AnyDesk foi encontrado na máquina PC-FINANCEIRO-01",
    "created_at": "2026-06-24T20:00:00"
  }
]
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

No MVP inicial, a API pode funcionar sem login apenas em ambiente local/laboratório.

Antes de expor na internet, será obrigatório implementar:

```text
API Key para agentes
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
Software suspeito
Firewall desativado
Defender desativado
RDP habilitado
Falhas excessivas de login
Novo administrador local
USB conectado
```

---

# Softwares Suspeitos Iniciais

```text
AnyDesk
TeamViewer
UltraViewer
RustDesk
Hamachi
uTorrent
BitTorrent
```

---

# Critério de Conclusão do MVP da API

A API estará pronta para o MVP quando:

* GET /health funcionar.
* POST /agent/checkin receber dados.
* Dados forem salvos no PostgreSQL.
* GET /machines listar máquinas.
* GET /machines/{id} detalhar máquina.
* GET /security-events listar eventos.
* GET /alerts listar alertas.
