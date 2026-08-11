# Backend

Esta pasta documenta os contratos do backend e do banco de dados.

## Documentos

| Documento | Conteudo |
| --- | --- |
| `API.md` | Endpoints e contratos HTTP. |
| `DATABASE.md` | Modelo relacional e tabelas. |

## Stack

```text
Python
FastAPI
PostgreSQL
psycopg
httpx      (necessario pelo TestClient do FastAPI/Starlette em testes)
reportlab  (relatorios PDF, app/services/reports.py — EPIC 20, ADR-029)
```

## Health check

```text
GET /api/v1/health
```

## Banco

O PostgreSQL e o Data Layer oficial do MVP. Ele nao deve ser exposto publicamente.

## Execucao e variaveis de ambiente

Guia completo de execucao (Docker Compose e manual) e lista de variaveis de ambiente: `backend/README.md`.
