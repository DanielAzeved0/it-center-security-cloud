# Fluxo de dados

Este documento descreve os principais fluxos de comunicacao do IT Center Security Cloud.

## Fluxo principal

```text
Windows Agent
    |
    | HTTPS + X-Agent-Api-Key
    v
Nginx
    |
    v
FastAPI Backend
    |
    v
PostgreSQL
    |
    v
Next.js Dashboard
```

## Check-in do agente

1. O agente coleta informacoes da maquina Windows.
2. O agente envia os dados para o endpoint de check-in.
3. O Nginx repassa a requisicao para o backend.
4. O backend valida `X-Agent-Api-Key`.
5. O backend valida o payload.
6. O backend persiste dados no PostgreSQL.
7. Eventos e alertas podem ser gerados.
8. Agenda sincronizacao com Snipe-IT via BackgroundTasks, sem bloquear a resposta (ADR-028).

Endpoint:

```text
POST /api/v1/agent/checkin
```

## Consulta do dashboard

1. O usuario acessa o dashboard por HTTPS.
2. O Nginx exige HTTP Basic Auth como camada extra de borda (paginas e assets estaticos; rotas `/api/backend/` ficam isentas por carregarem o Bearer token da aplicacao — ADR-023).
3. O usuario faz login administrativo na aplicacao (Bearer token HMAC SHA-256, RBAC admin/analyst/viewer — ver `docs/security/AUTH.md`).
4. O Nginx encaminha a requisicao para o Next.js.
5. O Next.js consulta o backend pela rede interna, repassando o Bearer token.
6. O backend valida o token/RBAC e consulta o PostgreSQL.
7. O dashboard renderiza maquinas, metricas, eventos e alertas.

## Dashboard executivo e relatorios (EPIC 20)

1. O usuario autenticado (`admin`/`analyst`/`viewer`) acessa a tela executiva no dashboard.
2. O Next.js chama `GET /api/v1/dashboard/summary` pelo proxy interno, repassando o Bearer token.
3. O backend agrega maquinas online/offline, alertas por severidade e eventos recentes (`app/services/dashboard.py` + `app/repositories/dashboard.py`) em uma unica resposta, evitando N chamadas do frontend.
4. Ao exportar PDF, o Next.js chama `GET /api/v1/reports/executive.pdf` ou `GET /api/v1/machines/{id}/report.pdf`, que o backend gera com `reportlab` (`app/services/reports.py`) e devolve como binario (o proxy repassa via `arrayBuffer`, nao `text()`, para nao corromper o PDF).

## Fluxo interno Docker

```text
nginx -> frontend:3000
nginx -> backend:8000
frontend -> backend:8000
backend -> postgres:5432
```

## Regras de exposicao

A tabela completa de portas publicas/internas e mantida em `docs/architecture/NETWORK.md` ("Publicacao de portas"), sem duplicacao aqui. Resumo: apenas o Nginx (80/443) e exposto; PostgreSQL, backend e frontend nao devem ser expostos diretamente na internet.
