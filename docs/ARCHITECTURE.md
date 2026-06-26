# ARCHITECTURE.md

# IT Center Security Cloud - Arquitetura Oficial

## Objetivo

Definir a arquitetura técnica oficial do IT Center Security Cloud para garantir:

* Simplicidade
* Escalabilidade futura
* Baixo custo
* Facilidade de manutenção
* Facilidade para novos contribuidores
* Compatibilidade com futuras funcionalidades de SOC

---

# Visão Geral da Arquitetura

O sistema será composto por 4 camadas principais:

```text
Agente Windows
        ↓
API Backend
        ↓
Banco PostgreSQL
        ↓
Dashboard Web
```

Fluxo completo:

```text
Windows PC
        ↓
PowerShell Agent
        ↓
HTTPS
        ↓
FastAPI
        ↓
PostgreSQL
        ↓
Dashboard Next.js
```

---

# Componentes

## 1. Agente Windows

Responsabilidade:

Coletar informações da máquina e enviá-las para a API.

Tecnologia:

* PowerShell

Motivos:

* Nativo do Windows
* Não exige instalação adicional
* Fácil distribuição

---

## Dados Coletados

### Inventário

```text
Hostname
Usuário
IP
Sistema Operacional
Versão Windows
CPU
RAM
Disco
```

### Monitoramento

```text
Uso de CPU
Uso de RAM
Uso de Disco
Uptime
Último Check-in
```

### Segurança

```text
Firewall
Windows Defender
Usuários Administradores
RDP
USB
Softwares Instalados
```

---

# Estrutura do Agente

```text
agent-windows/

├── itcenter-agent.ps1
├── config.json
├── logs/
└── cache/
```

---

# Configuração do Agente

config.json

```json
{
  "server_url": "https://api.itcenter.local",
  "agent_id": "HOST-001",
  "interval_minutes": 5
}
```

---

# Backend

Responsabilidade:

Receber informações do agente e disponibilizar para o dashboard.

Tecnologia:

* Python
* FastAPI

---

# Estrutura Backend

```text
backend/

app/

├── main.py
├── database.py
├── models/
├── schemas/
├── routes/
├── services/
├── repositories/
└── core/
```

Arquivos de runtime do backend:

```text
backend/
├── Dockerfile
├── apply_migrations.py
├── requirements.txt
└── migrations/
```

Quando o backend roda via Docker, `apply_migrations.py` executa as migrations SQL antes do Uvicorn iniciar.

---

# Camadas Backend

## Routes

Responsável por:

```text
Receber requisições HTTP
Validar entrada
Retornar resposta
```

---

## Services

Responsável por:

```text
Regras de negócio
Processamento
Validações
```

---

## Repositories

Responsável por:

```text
Acesso ao banco
Queries
Persistência
```

---

# Persistência Atual

O backend deve persistir dados no PostgreSQL por meio da camada `repositories`.

No estágio atual:

```text
POST /api/v1/agent/checkin
        ↓
routes/agent.py
        ↓
services/agent.py
        ↓
repositories/machines.py
        ↓
PostgreSQL
```

Responsabilidades da integração:

```text
Atualizar ou criar máquina em machines
Salvar coleta em metrics
Substituir snapshot atual de installed_programs
Sincronizar baseline de machine_local_admins
Criar agent_configs padrao no primeiro check-in
Gerar security_events conforme SOC_RULES.md
Gerar alerts conforme SOC_RULES.md
Ler máquinas em GET /api/v1/machines
Ler alertas em GET /api/v1/alerts
Ler eventos em GET /api/v1/security-events
```

Os repositórios em memória foram removidos da implementação principal.

---

## Models

Responsável por:

```text
Representação das tabelas
```

---

# Banco de Dados

Tecnologia:

PostgreSQL

---

# Tabelas

## machines

```text
id
hostname
username
ip
os
last_seen
status
created_at
updated_at
```

---

## metrics

```text
id
machine_id
cpu_usage
ram_usage
disk_usage
uptime
created_at
```

---

## installed_programs

```text
id
machine_id
name
version
publisher
```

---

## machine_local_admins

```text
id
machine_id
admin_name
first_seen_at
last_seen_at
```

---

## security_events

```text
id
machine_id
event_type
severity
source
description
raw_data
created_at
```

---

## alerts

```text
id
machine_id
alert_type
severity
status
title
description
created_at
resolved_at
```

---

## agent_configs

```text
id
machine_id
agent_version
checkin_interval_minutes
collect_inventory
collect_security
collect_metrics
created_at
updated_at
```

---

# API

Base URL

```text
/api/v1
```

---

## Health Check

GET

```text
/api/v1/health
```

Retorno:

```json
{
  "status": "healthy",
  "service": "it-center-security-cloud"
}
```

---

## Agent Check-in

POST

```text
/api/v1/agent/checkin
```

Responsável por:

```text
Receber dados do agente
Atualizar máquina
Salvar métricas
Gerar eventos
```

---

## Machines

GET

```text
/api/v1/machines
```

Lista máquinas cadastradas.

---

## Machine Details

GET

```text
/api/v1/machines/{id}
```

Retorna detalhes da máquina.

---

## Security Events

GET

```text
/api/v1/security-events
```

Lista eventos de segurança.

---

## Alerts

GET

```text
/api/v1/alerts
```

Lista alertas.

---

# Dashboard

Tecnologia:

* Next.js
* TypeScript
* CSS global proprio

---

# Estrutura Dashboard

```text
frontend/

dashboard/

├── app/
├── components/
├── lib/
├── public/
├── Dockerfile
├── package.json
└── next.config.mjs
```

O dashboard consome o backend por um proxy interno:

```text
Browser
    ->
Next.js /api/backend/...
    ->
FastAPI /api/v1/...
```

Em Docker Compose, o proxy usa:

```text
ITCENTER_API_BASE_URL=http://backend:8000
```

Em execucao local fora do Docker, o valor padrao e:

```text
http://127.0.0.1:8000
```

---

# Telas MVP

## Dashboard

```text
Total de Máquinas
Online
Offline
Último Check-in
```

---

## Inventário

```text
Lista de Máquinas
Sistema Operacional
Usuário
IP
```

---

## Monitoramento

```text
CPU
RAM
Disco
```

---

## Segurança

```text
Falhas de Login
USB
Softwares Suspeitos
Administradores
```

---

# Infraestrutura

Tecnologia:

* Docker
* Docker Compose
* Nginx
* Oracle Cloud

---

# Containers

## Backend

```text
FastAPI
```

---

## Banco

```text
PostgreSQL
```

---

## Frontend

```text
Next.js
```

---

## Proxy

```text
Nginx
```

---

# Docker Compose

Containers locais:

```text
postgres
backend
frontend
```

Fluxo local:

```text
docker compose
    ->
postgres fica healthy
    ->
backend aplica migrations e inicia FastAPI
    ->
frontend inicia Next.js apontando para backend
```

Portas locais:

```text
frontend: 127.0.0.1:3000
backend: 127.0.0.1:8000
postgres: 127.0.0.1:5432
```

Nginx permanece planejado para producao/cloud, conforme DEPLOYMENT.md.

---

# Roadmap Técnico

## Sprint 1

Infraestrutura Base

Entregas:

* Repositório
* Docker Compose
* PostgreSQL
* FastAPI

---

## Sprint 2

Primeira API

Entregas:

* Endpoint Health
* Endpoint Check-in

---

## Sprint 3

Agente

Entregas:

* Coleta básica
* Envio para API

---

## Sprint 4

Banco

Entregas:

* Persistência
* Consulta de máquinas

---

## Sprint 5

Dashboard

Entregas:

* Máquinas Online
* Inventário

---

## Sprint 6

SOC Light

Entregas:

* Eventos
* Alertas
* Segurança

---

# Critérios de Sucesso do MVP

O MVP será considerado concluído quando:

* O agente enviar dados.
* A API salvar dados.
* O banco persistir informações.
* O dashboard listar máquinas.
* O dashboard mostrar métricas básicas.
* O dashboard exibir eventos de segurança.

Fim da Arquitetura Oficial.
