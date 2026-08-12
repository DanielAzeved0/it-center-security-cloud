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

Camadas oficiais (detalhamento completo de cada camada em `docs/architecture/INFRASTRUCTURE.md` — não duplicado aqui):

* Edge Node: VM Ubuntu `itcenter-edge-01`, ponto operacional do MVP na Oracle Cloud.
* Infrastructure Layer: Docker Engine/Compose e rede/volumes do host.
* Platform Layer: Nginx, TLS e scripts operacionais de deploy/backup/restore/rollback.
* Application Layer: Next.js, FastAPI e agente Windows.
* Data Layer: PostgreSQL e backups.
* Security Layer: camada transversal de autenticação, rede e segredos.

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

O MVP é publicado em um único nó de borda (`itcenter-edge-01`), mantendo a aplicação monolítica e os serviços internos isolados da internet. A topologia de rede (VCN, subnets, gateways, IP público) é detalhada em `docs/architecture/NETWORK.md` — não duplicada aqui; o provisionamento dessa camada via Terraform está em `docs/architecture/IAC.md`.

Responsabilidades do `itcenter-edge-01`:

* Receber tráfego HTTPS pelo Nginx.
* Executar frontend, backend e PostgreSQL por Docker Compose na rede explícita `itcenter-network`.
* Manter apenas o Nginx exposto ao público.
* Aplicar migrations no início do backend.
* Manter PostgreSQL como Data Layer, separado conceitualmente da aplicação mesmo rodando no mesmo host.
* Executar preflight, deploy, rollback, backup e restore por scripts versionados em `infra/scripts`.

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

A fonte de verdade sobre schema, campos, índices e constraints é `docs/backend/DATABASE.md` (ver `docs/development/CONTRIBUTING.md`, seção "Fonte da Verdade"). Não duplique campos aqui — liste apenas os nomes das tabelas para orientação arquitetural:

```text
machines
metrics
installed_programs
machine_local_admins
security_events
alerts
agent_configs
users
audit_logs
```

---

# API

Base URL:

```text
/api/v1
```

A fonte de verdade sobre rotas, contratos de request/response e regras de segurança é `docs/backend/API.md`. Visão arquitetural por grupo de endpoints:

```text
/api/v1/health                          health check
/api/v1/auth/login, /me, /logout         login administrativo (Bearer HMAC, ADR-022)
/api/v1/agent/checkin                    check-in do agente (X-Agent-Api-Key)
/api/v1/machines, /machines/{id}         inventário de máquinas
/api/v1/machines/{id}/metrics            métricas históricas
/api/v1/machines/{id}/programs           programas instalados
/api/v1/machines/{id}/admins             administradores locais
/api/v1/machines/{id}/rustdesk (PATCH)   cadastro do ID do RustDesk (ADR-027)
/api/v1/security-events                  eventos de segurança (SOC Light)
/api/v1/alerts, /alerts/{id}/resolve     alertas e resolução
/api/v1/dashboard/summary                resumo agregado para o dashboard executivo (ADR-029)
/api/v1/reports/executive.pdf            relatório executivo em PDF (ADR-029)
/api/v1/machines/{id}/report.pdf         relatório em PDF de uma máquina (ADR-029)
```

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

A partir da ADR-024, a Infrastructure Layer abaixo do sistema operacional (VCN, subnets, security list, instância) é provisionada e versionada via Terraform, introduzido por `terraform import` sem destroy/recreate — ver `docs/architecture/IAC.md`.

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

O roadmap detalhado (fases e EPICs) vive em `docs/development/ROADMAP.md` e `docs/development/TASKS.md` — não duplicado aqui. Resumo histórico: a base do MVP (infraestrutura, primeira API, agente, banco, dashboard, SOC Light) corresponde às EPICs 1-6; produção, governança/autenticação e hardening vieram nas EPICs 7-18; a integração RustDesk (EPIC 19, ADR-027), os relatórios/dashboard executivo (EPIC 20, ADR-029) e o polimento visual do dashboard com GSAP (EPIC 24, ADR-035) já estão concluídos; a integração com Snipe-IT feita na mesma EPIC 19 (ADR-028) foi revertida em 2026-08-11 (ADR-033) por falta de necessidade concreta de ITAM. Observabilidade de infraestrutura via Prometheus/Grafana (EPIC 21, ADR-030), auto-atualização do agente Windows (EPIC 22, ADR-032) e auto-detecção do ID do RustDesk (EPIC 23, ADR-034) estão apenas planejadas, sem código ainda.

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
