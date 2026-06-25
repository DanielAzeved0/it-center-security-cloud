# Infra

Infraestrutura local do IT Center Security Cloud.

## PostgreSQL

Opcionalmente, crie um arquivo `.env` na raiz do projeto usando `.env.example` como base.
Se `.env` não existir, o Docker Compose usará os valores padrão definidos em `infra/docker-compose.yml`.

Subir o banco:

```powershell
docker compose -f infra/docker-compose.yml up -d postgres
```

Verificar status:

```powershell
docker compose -f infra/docker-compose.yml ps
```

Parar o banco:

```powershell
docker compose -f infra/docker-compose.yml down
```

Remover banco e volume local:

```powershell
docker compose -f infra/docker-compose.yml down -v
```
