# Migrations

Migrations SQL do PostgreSQL, aplicadas em ordem:

```text
001_initial_schema.sql   tabelas iniciais (machines, metrics, installed_programs, machine_local_admins, security_events, alerts, agent_configs)
002_users.sql             tabela users (login administrativo, RBAC — EPIC 12)
003_audit_logs.sql        tabela audit_logs (auditoria — EPIC 12)
004_machines_rustdesk.sql tabela machines ganha rustdesk_id (integração RustDesk — EPIC 19, ADR-027)
005_machines_snipeit.sql  tabela machines ganha snipeit_asset_id (integração Snipe-IT — EPIC 19, ADR-028)
006_remove_machines_snipeit.sql  remove snipeit_asset_id (integração revertida — ADR-033)
007_machines_mac_address.sql     tabela machines ganha mac_address (coleta no check-in do agente)
008_machines_serial_number.sql   tabela machines ganha serial_number (coleta no check-in do agente — EPIC 27)
009_machines_agent_secret.sql    tabela machines ganha agent_secret_hash (identidade por maquina no check-in — EPIC 28-A, ADR-036)
010_alerts_open_unique_index.sql índice parcial único em alerts para (machine_id, alert_type) com status open/investigating (EPIC 31, ADR-035)
011_installed_programs_publisher_unique.sql constraint única em installed_programs incluindo publisher para evitar colisões
012_machine_local_admins_case_insensitive.sql índice único em machine_local_admins com lower(admin_name) para unicidade case-insensitive
013_machines_agent_version.sql   tabela machines ganha agent_version e target_agent_version (auto-atualização do agente — EPIC 22, ADR-032)
014_create_revoked_tokens.sql    tabela revoked_tokens para revogação server-side de tokens Bearer no logout (EPIC 38, ADR-039)
015_add_installed_programs_hash.sql tabela machines ganha installed_programs_hash para fingerprinting de programas instalados (EPIC 40)
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
