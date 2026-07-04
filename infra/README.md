# Infra

Infraestrutura local e de producao do IT Center Security Cloud.

O arquivo `docker-compose.yml` é exclusivo para desenvolvimento local. Para publicar na Oracle Cloud, use `docker-compose.production.yml` e siga o procedimento em `docs/deployment/PRODUCTION.md`; não exponha o Compose local diretamente na internet.

## Bootstrap do Edge Node

O bootstrap versionado ainda esta documentado como proposta em:

```text
docs/deployment/BOOTSTRAP.md
```

A proposta define que a futura automacao deve preparar o Ubuntu Server do Edge Node antes do deploy dos containers:

* hostname, update e timezone;
* ferramentas operacionais;
* estrutura `/opt/itcenter`;
* Docker CE e Docker Compose Plugin;
* UFW;

Neste momento, os scripts ainda nao foram implementados. Clone do repositorio, `.env.production`, Compose, HTTPS e preflight pertencem ao fluxo de deploy documentado em `docs/deployment/PRODUCTION.md`.

## Servicos

O Docker Compose sobe:

```text
postgres  PostgreSQL
backend   FastAPI
frontend  Next.js
```

O backend aplica as migrations automaticamente antes de iniciar a API.

## Scripts de producao

Os scripts oficiais ficam em `infra/scripts/`:

```text
preflight-production.sh  valida prerequisitos de producao
deploy.sh                executa preflight, build, up, healthchecks e smoke tests
rollback.sh              retorna para um Git ref anterior preservando o banco
backup.sh                gera dump PostgreSQL compactado
restore.sh               restaura dump mediante confirmacao explicita
install-backup-cron.sh   instala backup periodico diario via cron
ops-check.sh             verifica disco, memoria, containers, TLS e backup recente
renew-tls.sh             renova certificado TLS e recarrega Nginx
docker-scout-gate.sh     executa gate Docker Scout critical/high
```

Na VM:

```bash
cd /opt/itcenter/app/it-center-security-cloud
sh infra/scripts/deploy.sh
```

Rotina operacional semanal:

```bash
sh infra/scripts/ops-check.sh
```

Runbook:

```text
docs/deployment/WEEKLY_OPERATIONS.md
```

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
