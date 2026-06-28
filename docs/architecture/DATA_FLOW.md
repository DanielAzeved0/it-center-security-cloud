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

Endpoint:

```text
POST /api/v1/agent/checkin
```

## Consulta do dashboard

1. O usuario acessa o dashboard por HTTPS.
2. O Nginx exige HTTP Basic Auth.
3. O Nginx encaminha a requisicao para o Next.js.
4. O Next.js consulta o backend pela rede interna.
5. O backend consulta o PostgreSQL.
6. O dashboard renderiza maquinas, metricas, eventos e alertas.

## Fluxo interno Docker

```text
nginx -> frontend:3000
nginx -> backend:8000
frontend -> backend:8000
backend -> postgres:5432
```

## Regras de exposicao

```text
Publico:
80/tcp
443/tcp

Interno:
3000/tcp
8000/tcp
5432/tcp
```

PostgreSQL, backend e frontend nao devem ser expostos diretamente na internet.
