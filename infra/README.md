# Infra

Infraestrutura local do IT Center Security Cloud.

O arquivo `docker-compose.yml` é exclusivo para desenvolvimento local. Para publicar na Oracle Cloud, use `docker-compose.production.yml` e siga o procedimento em `docs/DEPLOYMENT.md`; não exponha o Compose local diretamente na internet.

## Servicos

O Docker Compose sobe:

```text
postgres  PostgreSQL
backend   FastAPI
frontend  Next.js
```

O backend aplica as migrations automaticamente antes de iniciar a API.

## Subir tudo

Na raiz do projeto:

```powershell
cd "C:\Users\Famili Azevedo\Desktop\it-center-security-cloud"
docker compose -f infra/docker-compose.yml up --build
```

Em segundo plano:

```powershell
cd "C:\Users\Famili Azevedo\Desktop\it-center-security-cloud"
docker compose -f infra/docker-compose.yml up --build -d
```

## URLs locais

```text
Dashboard: http://127.0.0.1:3000
Backend:   http://127.0.0.1:8000/api/v1/health
Postgres:  127.0.0.1:5432
```

## Verificar status

```powershell
cd "C:\Users\Famili Azevedo\Desktop\it-center-security-cloud"
docker compose -f infra/docker-compose.yml ps
```

Logs:

```powershell
cd "C:\Users\Famili Azevedo\Desktop\it-center-security-cloud"
docker compose -f infra/docker-compose.yml logs -f backend frontend
```

## Parar

```powershell
cd "C:\Users\Famili Azevedo\Desktop\it-center-security-cloud"
docker compose -f infra/docker-compose.yml down
```

Remover banco e volume local:

```powershell
cd "C:\Users\Famili Azevedo\Desktop\it-center-security-cloud"
docker compose -f infra/docker-compose.yml down -v
```
