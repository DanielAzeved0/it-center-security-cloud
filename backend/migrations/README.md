# Migrations

Migrations SQL do PostgreSQL.

Aplicar a migration inicial com o container do PostgreSQL em execução:

```powershell
docker compose -f ..\infra\docker-compose.yml exec -T postgres psql -U itcenter -d it_center_security_cloud -f /migrations/001_initial_schema.sql
```

Enquanto o volume de migrations não estiver montado no container, use:

```powershell
Get-Content .\migrations\001_initial_schema.sql | docker compose -f ..\infra\docker-compose.yml exec -T postgres psql -U itcenter -d it_center_security_cloud
```
