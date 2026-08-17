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

# Observabilidade de Infraestrutura (EPIC 21, ADR-030)

`infra/docker-compose.production.yml` inclui quatro servicos adicionais — `node_exporter`, `cadvisor`, `prometheus` e `grafana` — sob `profiles: ["observability"]`, seguindo o mesmo padrao ja usado pelo `certbot` (`profiles: ["maintenance"]`): eles **nao** sobem com um `docker compose up` comum, exigindo `--profile observability` explicito do operador.

Escopo: saude do Edge Node (CPU/RAM/disco/rede da VM via `node_exporter`) e dos containers Docker (`cadvisor`) — nao substitui nem duplica a coleta de metricas por maquina Windows feita pelo agente (`metrics`, EPIC 3). Prometheus faz scrape dessas duas fontes com `scrape_interval: 30s` e retencao curta (`--storage.tsdb.retention.time=5d`, `--storage.tsdb.retention.size=200MB`); Grafana consome o Prometheus via datasource provisionado automaticamente e exibe um dashboard pre-configurado (`infra/observability/grafana/dashboards/edge-node-overview.json`).

Motivo do profile opt-in: a VM e Oracle Free Tier `VM.Standard.E2.1.Micro` com 1GB de RAM total, ja rodando justa com os 4 servicos atuais (ver `MEM_WARN_MB`/`MEM_FAIL_MB` em `infra/scripts/ops-check.sh`). Cada um dos 4 novos servicos tem `mem_limit` conservador (`node_exporter` ~30M, `cadvisor` ~100M, `prometheus` ~200M, `grafana` ~150M) para que nenhum sozinho derrube a VM por OOM. Validado na VM real em 2026-08-15 (`docker compose --profile observability up -d`): os 4 containers subiram healthy e `ops-check.sh` reportou `WARN` de memoria disponivel (424MB, acima do limite critico `MEM_FAIL_MB`) — risco de pressao de memoria aceito conscientemente e monitorado, ja nao uma pendencia de validacao (ver `docs/deployment/KNOWN_ISSUES.md`, "Observabilidade (EPIC 21): memoria em alerta com o profile ativo"). Decisao operacional: manter os 4 servicos ativos continuamente em producao.

Nenhum dos quatro publica porta no host: Nginx continua o unico ponto de entrada publico. Acesso operacional e via `docker exec` ou tunel SSH direto ao IP do container na rede `itcenter-network` — nunca por uma nova `location` no `nginx.conf.template` (ver `docs/architecture/NETWORK.md` e `docs/security/SECURITY.md`).

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

O roadmap detalhado (fases e EPICs) vive em `docs/development/ROADMAP.md` e `docs/development/TASKS.md` — não duplicado aqui. Resumo histórico: a base do MVP (infraestrutura, primeira API, agente, banco, dashboard, SOC Light) corresponde às EPICs 1-6; produção, governança/autenticação e hardening vieram nas EPICs 7-18; a integração RustDesk (EPIC 19, ADR-027), os relatórios/dashboard executivo (EPIC 20, ADR-029) e o polimento visual do dashboard com GSAP (EPIC 24, ADR-035) já estão concluídos; a integração com Snipe-IT feita na mesma EPIC 19 (ADR-028) foi revertida em 2026-08-11 (ADR-033) por falta de necessidade concreta de ITAM. Observabilidade de infraestrutura via Prometheus/Grafana (EPIC 21, ADR-030) foi ativada em produção em 2026-08-15 (profile `observability` em `infra/docker-compose.production.yml`; os 4 serviços — `node_exporter`, `cadvisor`, `prometheus`, `grafana` — validados na VM real e mantidos rodando continuamente por decisão operacional, apesar do alerta de memória aceito como risco, ver `docs/deployment/KNOWN_ISSUES.md`); auto-atualização do agente Windows (EPIC 22, ADR-032) e auto-detecção do ID do RustDesk (EPIC 23, ADR-034) permanecem apenas planejadas, sem código ainda. Depois da EPIC 24, a modernização visual do dashboard (EPIC 25) e o layout persistente de autenticação (EPIC 26) foram concluídas em 2026-08-12; a coleta do número de série da máquina pelo agente (EPIC 27) está implementada mas segue sem encerrar (falta validação em máquina virtual); e uma auditoria técnica de 2026-08-15 abriu seis EPICs de correção ainda pendentes de implementação — EPIC 28 (segurança), EPIC 29 (confiabilidade operacional de backup/restore), EPIC 30 (integridade de dados do backend), EPIC 31 (resiliência do agente Windows), EPIC 32 (aderência documentação-código) e EPIC 33 (cobertura de testes).

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
