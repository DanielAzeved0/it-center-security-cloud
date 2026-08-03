# Documentacao do IT Center Security Cloud

Este diretorio concentra a documentacao tecnica e operacional do projeto.

O objetivo e manter a documentacao simples, navegavel e suficiente para:

* entender a arquitetura;
* rodar o projeto localmente;
* operar a infraestrutura em producao;
* manter backend, banco, agente e seguranca;
* diagnosticar problemas comuns.

## Visao geral

O IT Center Security Cloud e uma plataforma para inventario, monitoramento e seguranca de maquinas Windows.

Arquitetura atual:

```text
Windows Agent
    |
    v
Nginx HTTPS
    |
    |-- Next.js Dashboard
    |
    `-- FastAPI Backend
            |
            v
        PostgreSQL
```

Em producao, todos os servicos rodam em Docker Compose na Oracle Cloud VM. Somente o Nginx expoe portas publicas.

## Indice

| Secao | Conteudo |
| --- | --- |
| `architecture/` | Arquitetura, infraestrutura e fluxo de dados. |
| `deployment/` | Setup, producao, troubleshooting, postmortems e diario de deploy. |
| `security/` | Politicas de seguranca, autenticacao e regras SOC. |
| `backend/` | API, banco de dados e contratos do backend. |
| `agent/` | Agente Windows, instalacao, preflight de conectividade e check-in. |
| `development/` | Contribuicao, roadmap, tarefas e decisoes. |
| `assets/` | Diagramas e imagens de apoio. |

## Guia rapido local

Na raiz do projeto:

```bash
cp .env.example .env
docker compose -f infra/docker-compose.yml up --build
```

URLs locais:

```text
Dashboard: http://127.0.0.1:3000
Backend:   http://127.0.0.1:8000/api/v1/health
Postgres:  127.0.0.1:5432
```

## Guia rapido de producao

Na VM:

```bash
cd /opt/itcenter/app/it-center-security-cloud
sh infra/scripts/preflight-production.sh
sh infra/scripts/deploy.sh
```

Validar:

```bash
docker ps
docker compose --env-file .env.production -f infra/docker-compose.production.yml ps
curl -I https://itcenter-daniel.chickenkiller.com
```

## Documentos principais

| Documento | Finalidade |
| --- | --- |
| `architecture/ARCHITECTURE.md` | Arquitetura oficial do sistema. |
| `architecture/DATA_FLOW.md` | Fluxos principais de comunicacao. |
| `architecture/FUTURE_ARCHITECTURE.md` | Plano de evolucao arquitetural futura. |
| `architecture/IAC.md` | Provisionamento via Terraform da infraestrutura Oracle Cloud (ADR-024). |
| `deployment/SETUP.md` | Preparacao do ambiente. |
| `deployment/PRODUCTION.md` | Estrategia e operacao de producao. |
| `deployment/TROUBLESHOOTING.md` | Diagnostico de falhas. |
| `deployment/OPERATIONAL_HANDOFF_2026-06-28.md` | Consolidado operacional do deploy real e integracao do agente. |
| `security/SECURITY.md` | Politicas de seguranca. |
| `security/AUTH.md` | Autenticacao do dashboard e do agente. |
| `backend/API.md` | Contrato da API. |
| `backend/DATABASE.md` | Modelo de dados. |
| `agent/CHECKIN.md` | Contrato do check-in do agente. |
| `agent/TROUBLESHOOTING.md` | Diagnostico operacional do agente Windows. |
| `development/CONTRIBUTING.md` | Regras de contribuicao. |
| `development/ROADMAP.md` | Roadmap do projeto. |
| `development/AI_WORKFLOW.md` | Orquestracao de agentes de IA no Claude Code (ADR-026). |

## Estado atual

```text
Infraestrutura: publicada
HTTPS: ativo
Dashboard: ativo
Backend: ativo
PostgreSQL: ativo
Windows Agent: integrado ao check-in de producao
```
