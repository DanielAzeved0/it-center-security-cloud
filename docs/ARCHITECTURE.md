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

## security_events

```text
id
machine_id
event_type
severity
description
created_at
```

---

## alerts

```text
id
machine_id
alert_type
status
created_at
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
  "status": "healthy"
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
* TailwindCSS

---

# Estrutura Dashboard

```text
frontend/

dashboard/

├── app/
├── components/
├── services/
├── hooks/
├── types/
└── pages/
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

Containers iniciais:

```text
backend
postgres
frontend
nginx
```

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
