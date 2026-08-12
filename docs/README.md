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

## Documentos mais consultados

Esta tabela nao tenta listar os 45 arquivos de `docs/` — isso ja provou decair rapido. E so um atalho para o que e consultado com mais frequencia no dia a dia:

| Documento | Finalidade |
| --- | --- |
| `deployment/PRODUCTION.md` | Estrategia e operacao de producao. |
| `deployment/TROUBLESHOOTING.md` | Diagnostico de falhas em producao. |
| `development/TASKS.md` | Backlog oficial, sempre atualizado. |
| `development/DECISIONS.md` | Registro de decisoes arquiteturais (ADRs). |
| `backend/API.md` | Contrato da API. |
| `backend/DATABASE.md` | Modelo de dados. |
| `security/AUTH.md` | Autenticacao do dashboard e do agente. |
| `security/ASSET_POLICY.md` | Fonte de verdade sobre softwares/ferramentas autorizados. |

A lista completa e sempre atualizada de cada pasta fica no `README.md` de cada subpasta (`agent/`, `architecture/`, `assets/`, `backend/`, `deployment/`, `development/`, `security/`) — cada um indexa 100% dos arquivos-irmaos.

## Estado atual

Ambiente publicado e operacional (HTTPS ativo, dashboard ativo, backend ativo, PostgreSQL ativo, agente Windows integrado ao check-in de producao). Progresso detalhado por EPIC esta em `development/TASKS.md` (backlog oficial, sempre atualizado).
