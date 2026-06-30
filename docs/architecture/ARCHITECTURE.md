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

O sistema segue uma arquitetura em camadas. No MVP, todas as camadas de runtime rodam no mesmo Edge Node, mas os limites ficam claros para permitir separação futura sem redesenhar o produto.

```text
Edge Node
    ↓
Infrastructure Layer
    ↓
Platform Layer
    ↓
Application Layer
    ↓
Data Layer
```

Camadas oficiais:

* Edge Node: VM Ubuntu `itcenter-edge-01`, ponto operacional do MVP na Oracle Cloud.
* Infrastructure Layer: Ubuntu Server 24.04, Docker Engine, Docker Compose v2, rede Docker `itcenter-network`, volume `postgres_data` e estrutura operacional `/opt/itcenter`.
* Platform Layer: Nginx, TLS com Let's Encrypt, reverse proxy, scripts de deploy, backup, restore e rollback.
* Application Layer: Next.js, FastAPI e agente Windows.
* Data Layer: PostgreSQL, volume `postgres_data`, migrations e dumps em `/opt/itcenter/backups`.
* Security Layer: camada transversal com firewall, Security Lists, HTTPS, Basic Auth, `X-Agent-Api-Key`, segredos fora do Git, hardening do Nginx e isolamento por rede Docker.

Fluxo funcional:

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

# Topologia de Produção do MVP

O MVP é publicado em um único nó de borda, mantendo a aplicação monolítica e os serviços internos isolados da internet.

```text
Internet
    ↓
IPv4 público
    ↓
Oracle Cloud VCN (10.0.0.0/16)
    ├── Subnet pública (10.0.0.0/24)
    │       ↓
    │   itcenter-edge-01 (Ubuntu Server 24.04)
    │       ├── Infrastructure: Docker Engine, Compose, itcenter-network, volumes
    │       ├── Platform: Nginx, TLS, reverse proxy
    │       ├── Application: Next.js, FastAPI
    │       ├── Data: PostgreSQL em postgres_data
    │       └── Security: firewall, HTTPS, Basic Auth, API Key, secrets
    │
    └── Subnet privada (10.0.1.0/24)
            └── Reservada para futura separação dos serviços
```

Responsabilidades do `itcenter-edge-01`:

* Receber tráfego HTTPS pelo Nginx.
* Executar frontend, backend e PostgreSQL por Docker Compose na rede explícita `itcenter-network`.
* Manter apenas o Nginx exposto ao público.
* Aplicar migrations no início do backend.
* Manter PostgreSQL como Data Layer, separado conceitualmente da aplicação mesmo rodando no mesmo host.
* Executar preflight, deploy, rollback, backup e restore por scripts versionados em `infra/scripts`.

A subnet privada não hospeda serviços no MVP. Ela é uma reserva de capacidade para migrar backend, frontend e PostgreSQL para instâncias privadas futuramente, preservando o `itcenter-edge-01` como ponto de entrada e proxy reverso.

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
  "server_url": "https://itcenter-daniel.chickenkiller.com",
  "agent_api_key": "<valor seguro>",
  "checkin_interval_minutes": 5,
  "log_path": "C:\\Program Files\\ITCenterAgent\\logs",
  "cache_path": "C:\\Program Files\\ITCenterAgent\\cache",
  "collect_inventory": true,
  "collect_metrics": true,
  "collect_security": true
}
```

Configs legadas com `api_key` e `interval_minutes` ainda podem ser aceitas pelo agente para compatibilidade, mas o schema oficial de producao usa `agent_api_key` e `checkin_interval_minutes`.

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

## Machine Metrics

GET

```text
/api/v1/machines/{id}/metrics
```

Lista metricas da maquina.

---

## Installed Programs

GET

```text
/api/v1/machines/{id}/programs
```

Lista programas instalados da maquina.

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

## Resolve Alert

PATCH

```text
/api/v1/alerts/{id}/resolve
```

Resolve um alerta aberto.

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

Camadas de infraestrutura no MVP:

```text
Edge Node: itcenter-edge-01
    └── Infrastructure Layer
            ├── Docker Engine
            ├── Docker Compose
            ├── Docker Network: itcenter-network
            ├── Volume nomeado: postgres_data
            └── Host layout: /opt/itcenter
```

O Compose de produção deve criar a rede `itcenter-network` explicitamente. Isso evita depender do nome gerado automaticamente pelo Compose e facilita troubleshooting, backup, monitoramento e futuras migrações.

Persistência e montagem:

* Dados do PostgreSQL usam o volume nomeado `postgres_data`.
* Configuração do Nginx, credencial Basic Auth, certificados Let's Encrypt e webroot do Certbot entram como bind mounts somente leitura quando usados pelo Nginx.
* Migrations do backend entram como bind mount somente leitura no PostgreSQL quando necessário.
* Logs de aplicação, Nginx e containers devem sair por `stdout`/`stderr`, permitindo coleta futura por Docker logs, Loki, Promtail ou outro agente.

Estrutura oficial do host:

```text
/opt/itcenter/
|-- app/       # clone do repositorio e Compose de producao
|-- backups/   # dumps compactados do PostgreSQL
|-- configs/   # configuracoes operacionais externas ao Git
|-- runtime/   # arquivos temporarios e estado operacional do host
|-- scripts/   # automacoes locais instaladas no host, quando necessario
|-- secrets/   # segredos externos ao Git, uso futuro
|-- logs/      # logs operacionais do host
`-- bin/       # wrappers ou atalhos administrativos locais
```

Scripts oficiais de producao:

* `infra/scripts/preflight-production.sh`: valida host, Compose, secrets, dominio, TLS, rede e volume.
* `infra/scripts/deploy.sh`: executa preflight, build, subida dos containers, healthchecks e smoke tests.
* `infra/scripts/rollback.sh`: retorna para um Git ref anterior preservando o volume `postgres_data`.
* `infra/scripts/backup.sh`: gera dump compactado do PostgreSQL com retencao configuravel.
* `infra/scripts/restore.sh`: restaura um dump mediante confirmacao explicita.

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

Em produção, o Nginx executa no `itcenter-edge-01` e é o único container com portas publicadas. A topologia de rede e a publicação estão descritas em `docs/deployment/PRODUCTION.md`.

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
