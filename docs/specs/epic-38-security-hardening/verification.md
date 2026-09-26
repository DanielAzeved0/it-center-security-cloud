# Verification: EPIC 38 - Seguranca da Aplicacao e Motor de Risco no Login (2026-09-26)

## Metadata

- Status: VERIFIED
- Data de Verificacao: 2026-09-26
- Escopo Verificado: 8 tarefas concluidas de forma atomica com TDD (Commits `60864ef`, `2d65c31`, `f468d2c`, `fd3b774`, `83e19c3`, `3482a84`, `4422ee6`, `c24696e`).
- Ambiente de Teste: Local Windows (.venv/Scripts/python.exe, pytest, PostgreSQL local Docker em 5432, Next.js build).

---

## Acceptance Criteria vs. Observed Evidence

### FR-001: Motor de Score de Risco no Login (Task 7 & Task 8)
- [x] **Janela deslizante de 1h & thread-safe**: Implementado em `backend/app/services/risk_engine.py` com locks de leitura/escrita.
- [x] **Heurísticas de Risco**:
  - Falha consecutiva: +20 pontos.
  - Velocidade em burst (> 3 requisicoes em 10s): +35 pontos.
  - Credential stuffing (>= 3 emails distintos: +30; >= 5 emails distintos: +50).
  - Email inexistente: +15 pontos.
- [x] **Bloqueio HTTP 429**: Ao atingir 100 pontos, bloqueia cliente por 15 minutos (900s) com header `Retry-After: 900`.
- [x] **Protecao contra DoS/Hash bypass**: Sob bloqueio 429, a requisicao e barrada imediatamente sem consulta ao banco nem execucao do PBKDF2.
- [x] **Log de auditoria**: Ao bloquear, registra acao `auth.login_blocked_risk` em `audit_logs`.
- [x] **Defesa em profundidade no Nginx**: Zona `login_limit:10m rate=10r/m` com `burst=5 nodelay` configurada em `infra/nginx/nginx.conf.template`.
- **Evidencia**: `backend/tests/test_risk_engine.py` e `backend/tests/test_auth_risk_login.py` passaram com 100% de sucesso.

### FR-002: Revogacao Real de Tokens no Logout (Task 5 & Task 6)
- [x] **Migration 014**: Tabela `revoked_tokens (token_hash VARCHAR(64) PRIMARY KEY, expires_at TIMESTAMPTZ NOT NULL)` e indice `idx_revoked_tokens_expires_at` criados e aplicados com sucesso.
- [x] **Repositorio**: `backend/app/repositories/revoked_tokens.py` implementa `revoke_token`, `is_token_revoked`, `purge_expired_revoked_tokens` em psycopg raw com context managers.
- [x] **Validacao no get_current_user**: Tokens revogados sao rejeitados com HTTP 401 Unauthorized imediatamente.
- [x] **Gravacao no Logout**: `POST /api/v1/auth/logout` calcula SHA-256 do token e persiste na tabela com data de expiracao extraida do claim `exp`.
- **Evidencia**: `backend/tests/test_revoked_tokens_repo.py` e `backend/tests/test_auth_logout_revocation.py` passaram com 100% de sucesso.

### FR-003: Validacao de Segredos em Producao (Task 1)
- [x] Rejeicao em producao para segredos com menos de 32 caracteres em `validate_runtime_configuration()`.
- **Evidencia**: `backend/tests/test_config.py` validado com sucesso.

### FR-004: Escape de Entradas no PDF (Task 2)
- [x] `backend/app/services/reports.py` utiliza `xml.sax.saxutils.escape` em hostnames, usernames e alertas antes de montar elementos `Paragraph()`.
- **Evidencia**: `backend/tests/test_reports.py` executado e aprovado.

### FR-005: Formato de rustdesk_id (Task 3)
- [x] Backend: `MachineRustdeskUpdate.rustdesk_id` valida regex `^\d{5,12}$`.
- [x] Frontend: `MachineDetailView.tsx` valida regex e aplica `encodeURIComponent` ao gerar link `rustdesk://connect?id=...`.
- **Evidencia**: `backend/tests/test_machine_schemas.py` aprovado.

### FR-006: Hardening do Proxy Next.js e Limpeza de Infra (Task 4)
- [x] `frontend/dashboard/app/api/backend/[...path]/route.ts`:
  - Rejeita requisicoes de escrita com `Content-Length > 1.048.576` com HTTP 413.
  - Rejeita requisicoes sem `Content-Type: application/json` com HTTP 415.
  - Repassa cabecalhos `X-Real-IP` e `User-Agent` para o backend FastAPI.
- [x] `NEXT_PUBLIC_API_BASE_URL` removido de `.env.example`, `.env.production.example`, `docker-compose.yml` e `docker-compose.production.yml`.
- **Evidencia**: `docker compose config` retornou exit code 0 e `npm run build` compilou com zero erros de tipo ou bundling.

---

## Automated Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.13.2, pytest-8.3.4
collected 177 items

backend/tests/test_agent_api.py .................
backend/tests/test_alerts.py ........
backend/tests/test_auth.py ...........
backend/tests/test_auth_logout_revocation.py ....
backend/tests/test_auth_risk_login.py ....
backend/tests/test_commands.py ..........
backend/tests/test_config.py .....
backend/tests/test_dashboard_metrics.py ....
backend/tests/test_database.py ..
backend/tests/test_export.py ....
backend/tests/test_incident_service.py .....
backend/tests/test_incidents_api.py .........
backend/tests/test_machine_schemas.py ....
backend/tests/test_machines.py ..............
backend/tests/test_machines_pagination.py ....
backend/tests/test_metrics.py .....
backend/tests/test_multi_tenancy.py .......
backend/tests/test_notification_service.py ........
backend/tests/test_org_switch.py ...
backend/tests/test_pdf_report.py .....
backend/tests/test_reports.py ...
backend/tests/test_revoked_tokens_repo.py ...
backend/tests/test_risk_engine.py .......
backend/tests/test_rules_service.py .......
backend/tests/test_script_service.py ......
backend/tests/test_soc_rules.py ......
backend/tests/test_users.py ...........

============================= 177 passed in 27.55s =============================
```

---

## Conclusao e Sign-off

Todas as 8 tarefas da EPIC 38 foram completamente implementadas, testadas com TDD, verificadas regressivamente e commitadas na branch principal (`main`).
O sistema esta pronto para publicacao e deploy via CI/CD.
