# Migrations

Migrations SQL do PostgreSQL, aplicadas em ordem:

```text
001_initial_schema.sql   tabelas iniciais (machines, metrics, installed_programs, machine_local_admins, security_events, alerts, agent_configs)
002_users.sql             tabela users (login administrativo, RBAC — EPIC 12)
003_audit_logs.sql        tabela audit_logs (auditoria — EPIC 12)
```

Em execução normal (Docker Compose ou `python apply_migrations.py`), todas as migrations são aplicadas automaticamente antes da API iniciar.

Aplicar uma migration manualmente com o container do PostgreSQL em execução:

```powershell
docker compose -f ..\infra\docker-compose.yml exec -T postgres psql -U itcenter -d it_center_security_cloud -f /migrations/001_initial_schema.sql
```

Enquanto o volume de migrations não estiver montado no container, use:

```powershell
Get-Content .\migrations\001_initial_schema.sql | docker compose -f ..\infra\docker-compose.yml exec -T postgres psql -U itcenter -d it_center_security_cloud
```
