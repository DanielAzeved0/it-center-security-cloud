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
```

## Health check

```text
GET /api/v1/health
```

## Banco

O PostgreSQL e o Data Layer oficial do MVP. Ele nao deve ser exposto publicamente.
