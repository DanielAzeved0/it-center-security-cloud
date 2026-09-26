# Spec: EPIC 38 - Seguranca da Aplicacao e Motor de Risco no Login (2026-09-26)

## Metadata

- Status: SPECIFIED (aguardando aprovacao para implementacao via writing-plans)
- Nivel de rigor: 3 (arquitetural) — altera fluxo de autenticacao, schema de banco de dados (tabela nova de revogacao de tokens), politicas de Nginx e contratos de proxy.
- Autor/origem: Auditoria de qualidade de 2026-08-20 (`docs/development/TASKS.md`, EPIC 38) + decisoes de design da sessao 2026-09-26 (motor de score de risco e bloqueio 429).
- Data: 2026-09-26
- Dependencias: EPIC 28 (timing-safe login), EPIC 30 (migrations idempotentes), EPIC 37 (Nginx proxy rules).

## Context

A auditoria de seguranca identificou lacunas defensivas em multiplos pontos do sistema:
1. `POST /api/v1/auth/login` nao possui rate limiting nem protecao contra ataques de forca bruta ou credential stuffing distribuido.
2. `AUTH_TOKEN_SECRET` e `AGENT_API_KEY` nao validavam comprimento minimo, permitindo segredos fracos vulneraveis a forca bruta offline.
3. `build_machine_report_pdf` interpolava `hostname` sem escape em `Paragraph()`, permitindo quebra de geracao de PDF ou injecao de pseudo-XML/links maliciosos.
4. `MachineRustdeskUpdate.rustdesk_id` nao possuia restricao de formato regex nem sanitizacao no frontend antes de montar a URI customizada `rustdesk://`.
5. O logout (`POST /api/v1/auth/logout`) era stateless e nao revogava tokens Bearer ativos antes de sua expiracao natural.
6. O proxy do dashboard (`route.ts`) nao validava `Content-Type`, nao impunha teto de tamanho de corpo (`Content-Length`) e nao repassava `X-Real-IP`/`User-Agent` para o backend FastAPI.
7. Variavel obsoleta `NEXT_PUBLIC_API_BASE_URL` ainda constava em arquivos de configuracao.

## Goal

Blindar a superficie de autenticacao e APIs do sistema:
1. Implementar um motor de score de risco em memoria no login com bloqueio rigido HTTP 429 para clientes maliciosos e log de auditoria no PostgreSQL.
2. Implementar revogacao real de tokens no logout atraves de tabela `revoked_tokens` no PostgreSQL.
3. Forcar falha rapida na inicializacao caso segredos de producao tenham menos de 32 caracteres.
4. Escapar entradas de usuario no ReportLab com `xml.sax.saxutils.escape`.
5. Validar formato estrito de `rustdesk_id` no schema e no frontend.
6. Proteger o proxy Next.js com validacao de `Content-Type`, limite de 1MB e repasse correto de IP/User-Agent.
7. Remover declaracoes residuais de `NEXT_PUBLIC_API_BASE_URL`.

## Scope

- **Trilha 1: Motor de Risco e Rate Limiting no Login**
  - Modulo `backend/app/services/risk_engine.py` (janela deslizante em memoria de 1h, calculo de score, bloqueio 15 min).
  - Integracao em `backend/app/routes/auth.py` (`POST /login` checa risco antes e pontua falhas).
  - Repasse de `X-Real-IP` e `User-Agent` em `frontend/dashboard/app/api/backend/[...path]/route.ts`.
  - Zona de seguranca `limit_req_zone` no `infra/nginx/nginx.conf.template` para defesa em profundidade.
- **Trilha 2: Revogacao de Tokens no Logout**
  - Migration `backend/migrations/014_create_revoked_tokens.sql` (tabela idempotente `revoked_tokens` e indice).
  - Repositorio `backend/app/repositories/revoked_tokens.py` (insert, check e purga de expirados).
  - Atualizacao de `backend/app/services/auth.py` (`get_current_user` consulta se token esta revogado).
  - Atualizacao de `backend/app/routes/auth.py` (`POST /logout` registra revogacao).
- **Trilha 3: Validacao de Segredos em Producao**
  - `backend/app/core/config.py`: verificar comprimento minimo de 32 caracteres em `validate_runtime_configuration()`.
- **Trilha 4: Sanitizacao de Relatorio PDF**
  - `backend/app/services/reports.py`: sanitizar com `xml.sax.saxutils.escape` campos dinamicos interpolados em `Paragraph()`.
- **Trilha 5: Validacao de `rustdesk_id` nas Duas Pontas**
  - `backend/app/schemas/machine.py`: regex `^\d{5,12}$` no campo `rustdesk_id`.
  - `frontend/dashboard/components/MachineDetailView.tsx`: validacao regex e `encodeURIComponent` ao montar o link `rustdesk://`.
- **Trilha 6: Hardening do Proxy Next.js e Limpeza de Infra**
  - `frontend/dashboard/app/api/backend/[...path]/route.ts`: teto 1MB e `Content-Type: application/json`.
  - Remocao de `NEXT_PUBLIC_API_BASE_URL` em `docker-compose.production.yml`, `docker-compose.yml`, `.env.example`, `.env.production.example`.

## Out of Scope

- Servidores de cache externo (Redis, Memcached) — a arquitetura permanece 100% contida na stack existente (FastAPI em memoria + PostgreSQL).
- Mudanca no algoritmo de hash de senhas (PBKDF2 SHA-256 com 210.000 iteracoes permanece inalterado).
- Autenticacao multifator (MFA/2FA) para usuarios do painel — melhoria futura fora do MVP.

## Functional Requirements

```
FR-001: Motor de Score de Risco no Login
- O sistema deve rastrear tentativas de login por IP e fingerprint de dispositivo em janela deslizante de 1 hora.
- Tentativas falhas consecutivas somam +20 pontos.
- Tentativas com > 3 requisicoes em 10 segundos somam +35 pontos (burst).
- Tentativas visando 3 ou mais e-mails distintos a partir do mesmo IP/dispositivo somam +30 pontos; >= 5 e-mails somam +50 pontos (credential stuffing).
- Tentativas contra e-mails inexistentes somam +15 pontos.
- Quando o score atinge ou supera 100 pontos, o IP/dispositivo e bloqueado por 15 minutos, retornando HTTP 429 Too Many Requests com header Retry-After: 900.
- Requisicoes sob bloqueio 429 nao executam consultas no PostgreSQL nem processam o hash PBKDF2.
- Um login com sucesso zera a pontuacao de risco acumulada para aquele IP e dispositivo.
- Bloqueios geram registro em audit_logs com action="auth.login_blocked_risk".

FR-002: Revogacao de Tokens no Logout
- Ao executar POST /api/v1/auth/logout com token valido, o hash SHA-256 do token deve ser persistido em revoked_tokens.
- Qualquer requisicao subsequente utilizando o mesmo token Bearer deve ser rejeitada com HTTP 401 Unauthorized.
- Tokens expirados (expires_at < NOW()) devem ser removidos periodicamente para evitar crescimento indefinido da tabela.

FR-003: Validacao de Tamanho de Segredos em Producao
- Em APP_ENV=production, validate_runtime_configuration() deve rejeitar AUTH_TOKEN_SECRET ou AGENT_API_KEY com menos de 32 caracteres levantando RuntimeError.

FR-004: Escape de Entradas no PDF
- build_machine_report_pdf deve escapar todos os campos textuais de maquina/usuario interpolados em Paragraph() com xml.sax.saxutils.escape.

FR-005: Formato de rustdesk_id
- MachineRustdeskUpdate deve rejeitar qualquer rustdesk_id que nao case com ^\d{5,12}$ retornando HTTP 422 Unprocessable Entity.
- O dashboard nao deve renderizar link clicavel para valores fora desse formato e deve aplicar encodeURIComponent ao gerar a URI.

FR-006: Hardening do Proxy Next.js
- proxyRequest deve rejeitar Content-Length > 1.048.576 bytes com HTTP 413 Payload Too Large antes de ler o corpo.
- Metodos de escrita (POST, PATCH) devem rejeitar Content-Type ausente ou diferente de application/json com HTTP 415.
- fetchUpstream deve repassar X-Real-IP e User-Agent do cliente original.
```

## Architecture & Data Design

### 1. Schema do Banco (`backend/migrations/014_create_revoked_tokens.sql`)
```sql
CREATE TABLE IF NOT EXISTS revoked_tokens (
    token_hash VARCHAR(64) PRIMARY KEY,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_revoked_tokens_expires_at ON revoked_tokens (expires_at);
```

### 2. Risk Engine (`backend/app/services/risk_engine.py`)
Classe singleton thread-safe `LoginRiskEngine` mantendo:
- `_events: dict[str, list[LoginAttemptRecord]]`
- `_blocks: dict[str, float]` (chave -> timestamp de expiracao do bloqueio)
Metodos:
- `inspect_client(ip: str, fingerprint: str) -> tuple[bool, int, int]` (is_blocked, current_score, retry_after)
- `record_attempt(ip: str, fingerprint: str, email: str, success: bool, user_exists: bool) -> int`
- `cleanup_expired() -> None`

## Testing Strategy

- `test_login_risk_score_blocks_after_threshold`: simula acumulo de score ate >= 100 e valida emissao de HTTP 429 com Retry-After.
- `test_login_credential_stuffing_detection`: simula mesmo IP testando 5 e-mails diferentes e valida bloqueio.
- `test_token_revocation_on_logout`: emite token, faz logout, tenta acessar `/api/v1/auth/me` e valida HTTP 401.
- `test_validate_runtime_configuration_secrets_length`: valida que segredos < 32 caracteres levantam `RuntimeError` em modo producao.
- `test_reportlab_hostname_escapes_xml`: gera relatorio com hostname contendo `<script>` e `<b>malicioso</b>` e valida parsing sem erro e sem injecao.
- `test_rustdesk_id_validation_backend`: valida rejeicao de strings alfanumericas, espacos ou caracteres especiais.
- `test_proxy_route_rejects_large_body_and_invalid_content_type`: testes de unidade e integracao no Next.js proxy.
