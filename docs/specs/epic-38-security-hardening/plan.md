# Plano de Implementação: EPIC 38 - Hardening de Segurança e Motor de Risco no Login

> **Para agentes executores:** SUB-SKILL OBRIGATÓRIA: Use superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans para implementar este plano tarefa por tarefa. As etapas usam sintaxe de checkbox (`- [ ]`) para rastreamento.

**Objetivo:** Implementar o hardening abrangente de segurança na plataforma IT Center Security Cloud: motor de rate limiting e avaliação de risco no login com bloqueio HTTP 429, revogação real de tokens no logout via PostgreSQL, validação estrita de comprimento mínimo de segredos em produção, escape de XML na geração de relatórios PDF com ReportLab, validação estrita por regex para `rustdesk_id` em ambas as pontas, e proteção de cabeçalhos/payload no proxy Next.js.

**Arquitetura:** Um motor leve em memória com janela deslizante (`LoginRiskEngine`) avalia IP do cliente, fingerprint de dispositivo, velocidade de rajada (burst) e padrões de credential stuffing sem sobrecarregar o PostgreSQL. Limiares excedidos acionam resposta imediata HTTP 429. A revogação de tokens persiste hashes SHA-256 em uma tabela idempotente `revoked_tokens` no PostgreSQL, consultada em `get_current_user`. Todas as entradas dinâmicas em `Paragraph()` do ReportLab são sanitizadas com `xml.sax.saxutils.escape`. O proxy Next.js valida `Content-Type` e impõe limite de 1MB no corpo da requisição, repassando `X-Real-IP` e `User-Agent`.

**Stack Técnica:** Python 3.13, FastAPI, PostgreSQL (psycopg 3 raw SQL), Next.js 16 (App Router / TypeScript), ReportLab, Nginx.

**Especificação:** [`docs/specs/epic-38-security-hardening/spec.md`](file:///C:/Users/gizad/it-center-security-cloud/docs/specs/epic-38-security-hardening/spec.md)

## Restrições Globais

- Sem servidores de cache externo ou filas de mensagens (sem Redis, Memcached, RabbitMQ) — execução contida na memória Python + PostgreSQL na VM de 1GB de RAM.
- Todas as operações no PostgreSQL usam queries brutas com `psycopg`; zero ORM.
- Zero quebras de compatibilidade nas rotas existentes de check-in do agente ou nos tokens de sessão ativos de usuários.
- TDD estrito: testes escritos e confirmados falhando antes de implementar o código mínimo.

---

### Tarefa 1: Validação de Comprimento de Segredos na Configuração de Produção

**Arquivos:**
- Modificar: `backend/app/core/config.py:19-38`
- Testar: `backend/tests/test_config.py`

**Interfaces:**
- Consome: `Settings.validate_runtime_configuration()`
- Produz: `RuntimeError` se `AUTH_TOKEN_SECRET` ou `AGENT_API_KEY` tiver comprimento < 32 quando `app_env == "production"`.

- [ ] **Passo 1: Escrever o teste que falha**

Criar/atualizar `backend/tests/test_config.py`:
```python
import pytest
from app.core.config import Settings


def test_validate_runtime_configuration_rejects_short_secrets(monkeypatch):
    settings = Settings()
    settings.app_env = "production"
    settings.auth_token_secret = "short-secret"
    settings.agent_api_key = "a" * 32
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@127.0.0.1:5432/db")

    with pytest.raises(RuntimeError, match="AUTH_TOKEN_SECRET must be at least 32 characters"):
        settings.validate_runtime_configuration()

    settings.auth_token_secret = "a" * 32
    settings.agent_api_key = "short-key"
    with pytest.raises(RuntimeError, match="AGENT_API_KEY must be at least 32 characters"):
        settings.validate_runtime_configuration()
```

- [ ] **Passo 2: Executar o teste para verificar a falha**

Comando: `pytest backend/tests/test_config.py -q`
Esperado: FAIL com `Failed: DID NOT RAISE <class 'RuntimeError'>`

- [ ] **Passo 3: Implementar a validação de comprimento de segredos**

Modificar `backend/app/core/config.py`:
```python
        if self.agent_api_key in insecure_values or len(self.agent_api_key or "") < 32:
            raise RuntimeError("AGENT_API_KEY must be configured with a non-default value of at least 32 characters in production")

        if self.auth_token_secret in insecure_values or len(self.auth_token_secret or "") < 32:
            raise RuntimeError("AUTH_TOKEN_SECRET must be configured with a non-default value of at least 32 characters in production")
```

- [ ] **Passo 4: Executar o teste para verificar aprovação**

Comando: `pytest backend/tests/test_config.py -q`
Esperado: PASS

- [ ] **Passo 5: Commit**

```bash
git add backend/app/core/config.py backend/tests/test_config.py
git commit -m "feat(security): enforce minimum 32 chars for production secrets in config"
```

---

### Tarefa 2: Escape de XML para Valores Dinâmicos na Geração de PDF com ReportLab

**Arquivos:**
- Modificar: `backend/app/services/reports.py:114-140`
- Testar: `backend/tests/test_reports.py`

**Interfaces:**
- Consome: `xml.sax.saxutils.escape`
- Produz: Elementos `Paragraph` sanitizados em `build_machine_report_pdf` que nunca disparam `ValueError` por entidades ou tags XML malformadas.

- [ ] **Passo 1: Escrever o teste que falha**

Em `backend/tests/test_reports.py`:
```python
from datetime import datetime, timezone
from app.schemas.machine import MachineDetail
from app.services.reports import build_machine_report_pdf


def test_build_machine_report_pdf_escapes_xml_tags_in_hostname():
    malicious_hostname = "PC-CORP<script>alert(1)</script>&<b>test</b>"
    machine = MachineDetail(
        id=1,
        hostname=malicious_hostname,
        ip_address="192.168.1.50",
        operating_system="Windows 11 Pro",
        os_version="10.0.22631",
        status="online",
        last_seen=datetime.now(timezone.utc),
        agent_version="1.0.0",
        rustdesk_id=None,
    )
    pdf_bytes = build_machine_report_pdf(
        machine=machine,
        metrics=[],
        programs=[],
        admins=[],
        alerts=[],
        events=[],
    )
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")
```

- [ ] **Passo 2: Executar o teste para verificar a falha**

Comando: `pytest backend/tests/test_reports.py::test_build_machine_report_pdf_escapes_xml_tags_in_hostname -q`
Esperado: FAIL ou exceção de parsing de XML do ReportLab.

- [ ] **Passo 3: Implementar o escape em reports.py**

Modificar `backend/app/services/reports.py`:
Importar `from xml.sax.saxutils import escape as xml_escape`.
Em `build_machine_report_pdf`:
Escapar `machine.hostname`, `machine.username` e qualquer string dinâmica passada a `Paragraph(...)`.

- [ ] **Passo 4: Executar o teste para verificar aprovação**

Comando: `pytest backend/tests/test_reports.py -q`
Esperado: PASS

- [ ] **Passo 5: Commit**

```bash
git add backend/app/services/reports.py backend/tests/test_reports.py
git commit -m "fix(reports): escape dynamic text in ReportLab Paragraph elements"
```

---

### Tarefa 3: Validação de Formato de `rustdesk_id` no Backend e Sanitização no Frontend

**Arquivos:**
- Modificar: `backend/app/schemas/machine.py:45-48`
- Modificar: `frontend/dashboard/components/MachineDetailView.tsx:300-320`
- Testar: `backend/tests/test_machine_schemas.py`
- Testar: `frontend/dashboard/__tests__/rustdesk_validation.test.ts`

**Interfaces:**
- Consome: Pydantic `Field(pattern=r"^\d{5,12}$")`
- Produz: `rustdesk_id` validado em `MachineRustdeskUpdate`; URI segura `rustdesk://connect?id=...` na interface.

- [ ] **Passo 1: Escrever o teste que falha no backend**

Criar `backend/tests/test_machine_schemas.py`:
```python
import pytest
from pydantic import ValidationError
from app.schemas.machine import MachineRustdeskUpdate


def test_machine_rustdesk_update_validates_numeric_format():
    valid = MachineRustdeskUpdate(rustdesk_id="123456789")
    assert valid.rustdesk_id == "123456789"

    none_valid = MachineRustdeskUpdate(rustdesk_id=None)
    assert none_valid.rustdesk_id is None

    with pytest.raises(ValidationError):
        MachineRustdeskUpdate(rustdesk_id="invalid-id")

    with pytest.raises(ValidationError):
        MachineRustdeskUpdate(rustdesk_id="123")

    with pytest.raises(ValidationError):
        MachineRustdeskUpdate(rustdesk_id="1234567890123")
```

- [ ] **Passo 2: Executar o teste para verificar a falha**

Comando: `pytest backend/tests/test_machine_schemas.py -q`
Esperado: FAIL

- [ ] **Passo 3: Atualizar schema e frontend**

Em `backend/app/schemas/machine.py`:
```python
class MachineRustdeskUpdate(BaseModel):
    rustdesk_id: str | None = Field(default=None, pattern=r"^\d{5,12}$")
```

Em `frontend/dashboard/components/MachineDetailView.tsx`:
Adicionar guarda com regex:
```tsx
const isValidRustdeskId = detail.rustdesk_id ? /^\d{5,12}$/.test(detail.rustdesk_id) : false;
```
Renderizar o link ativo de conexão apenas se `isValidRustdeskId && canManageRustdesk`, aplicando escape:
```tsx
href={`rustdesk://connect?id=${encodeURIComponent(detail.rustdesk_id)}`}
```

- [ ] **Passo 4: Executar os testes do backend**

Comando: `pytest backend/tests/test_machine_schemas.py -q`
Esperado: PASS

- [ ] **Passo 5: Commit**

```bash
git add backend/app/schemas/machine.py backend/tests/test_machine_schemas.py frontend/dashboard/components/MachineDetailView.tsx
git commit -m "feat(security): enforce numeric format for rustdesk_id on backend and frontend"
```

---

### Tarefa 4: Hardening do Proxy Next.js e Limpeza de Variáveis de Ambiente

**Arquivos:**
- Modificar: `frontend/dashboard/app/api/backend/[...path]/route.ts:90-110, 175-200`
- Modificar: `infra/docker-compose.production.yml`
- Modificar: `infra/docker-compose.yml`
- Modificar: `.env.example`
- Modificar: `.env.production.example`

**Interfaces:**
- Consome: Cabeçalhos da requisição no Next.js
- Produz: Requisições repassadas com `X-Real-IP` e `User-Agent`; rejeita payloads > 1MB com status 413, e Content-Type inválido com status 415.

- [ ] **Passo 1: Implementar checagem de tamanho de payload e Content-Type no proxy**

Em `frontend/dashboard/app/api/backend/[...path]/route.ts`:
Em `fetchUpstream`:
Adicionar repasse de `X-Real-IP` e `User-Agent`:
```ts
    headers: {
      "Content-Type": request.headers.get("Content-Type") ?? "application/json",
      "X-Real-IP": request.headers.get("x-real-ip") ?? request.headers.get("x-forwarded-for")?.split(",")[0].trim() ?? "127.0.0.1",
      "User-Agent": request.headers.get("user-agent") ?? "itcenter-dashboard",
      ...(sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {}),
    },
```
Em `proxyRequest`:
Antes de ler o corpo:
```ts
  if (request.method !== "GET" && request.method !== "HEAD") {
    const contentLength = request.headers.get("content-length");
    if (contentLength && parseInt(contentLength, 10) > 1024 * 1024) {
      return NextResponse.json({ detail: "Payload too large" }, { status: 413 });
    }
    const contentType = request.headers.get("content-type");
    if (contentType && !contentType.toLowerCase().includes("application/json")) {
      return NextResponse.json({ detail: "Unsupported Media Type" }, { status: 415 });
    }
  }
```

- [ ] **Passo 2: Limpar a variável obsoleta `NEXT_PUBLIC_API_BASE_URL`**

Remover `NEXT_PUBLIC_API_BASE_URL` de:
- `infra/docker-compose.production.yml`
- `infra/docker-compose.yml`
- `.env.example`
- `.env.production.example`

- [ ] **Passo 3: Executar validação de configuração do Docker Compose**

Comando: `docker compose -f infra/docker-compose.yml config -q`
Esperado: PASS (código de saída 0)

- [ ] **Passo 4: Commit**

```bash
git add frontend/dashboard/app/api/backend/[...path]/route.ts infra/docker-compose.production.yml infra/docker-compose.yml .env.example .env.production.example
git commit -m "feat(proxy): harden request proxying with size and content-type validation and header forwarding"
```

---

### Tarefa 5: Migração 014 e Repositório de Tokens Revogados

**Arquivos:**
- Criar: `backend/migrations/014_create_revoked_tokens.sql`
- Criar: `backend/app/repositories/revoked_tokens.py`
- Testar: `backend/tests/test_revoked_tokens_repo.py`

**Interfaces:**
- Produz:
  - `revoke_token(token_hash: str, expires_at: datetime) -> None`
  - `is_token_revoked(token_hash: str) -> bool`
  - `purge_expired_revoked_tokens() -> int`

- [ ] **Passo 1: Escrever a migração `014`**

Criar `backend/migrations/014_create_revoked_tokens.sql`:
```sql
CREATE TABLE IF NOT EXISTS revoked_tokens (
    token_hash VARCHAR(64) PRIMARY KEY,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_revoked_tokens_expires_at ON revoked_tokens (expires_at);
```

- [ ] **Passo 2: Escrever testes do repositório**

Criar `backend/tests/test_revoked_tokens_repo.py`:
```python
from datetime import datetime, timedelta, timezone
from app.repositories.revoked_tokens import is_token_revoked, purge_expired_revoked_tokens, revoke_token


def test_revoke_token_and_check():
    token_hash = "abc123testtokenhash0000000000000000000000000000000000000000000000"
    expires = datetime.now(timezone.utc) + timedelta(hours=1)

    assert not is_token_revoked(token_hash)
    revoke_token(token_hash, expires)
    assert is_token_revoked(token_hash)
```

- [ ] **Passo 3: Implementar `backend/app/repositories/revoked_tokens.py`**

Implementar `revoke_token`, `is_token_revoked` (com `ON CONFLICT DO NOTHING`) e `purge_expired_revoked_tokens` utilizando `get_connection()`.

- [ ] **Passo 4: Aplicar migração e testar repositório**

Comando:
```bash
python backend/apply_migrations.py
pytest backend/tests/test_revoked_tokens_repo.py -q
```
Esperado: PASS

- [ ] **Passo 5: Commit**

```bash
git add backend/migrations/014_create_revoked_tokens.sql backend/app/repositories/revoked_tokens.py backend/tests/test_revoked_tokens_repo.py
git commit -m "feat(auth): create revoked_tokens table and repository"
```

---

### Tarefa 6: Revogação de Tokens no Serviço de Autenticação e Endpoint de Logout

**Arquivos:**
- Modificar: `backend/app/services/auth.py:125-145`
- Modificar: `backend/app/routes/auth.py:85-99`
- Testar: `backend/tests/test_auth_logout_revocation.py`

**Interfaces:**
- Consome: `revoke_token`, `is_token_revoked`
- Produz: `get_current_user` validando revogação; `POST /logout` revogando o Bearer token ativo de quem chamou.

- [ ] **Passo 1: Escrever teste de integração que falha para revogação no logout**

Criar `backend/tests/test_auth_logout_revocation.py`:
```python
def test_logout_revokes_token_immediately(client, auth_headers):
    me_resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_resp.status_code == 200

    logout_resp = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert logout_resp.status_code == 200

    second_me = client.get("/api/v1/auth/me", headers=auth_headers)
    assert second_me.status_code == 401
```

- [ ] **Passo 2: Executar o teste para verificar a falha**

Comando: `pytest backend/tests/test_auth_logout_revocation.py -q`
Esperado: FAIL (segunda chamada a `/me` retorna 200 em vez de 401)

- [ ] **Passo 3: Implementar checagem de revogação em `get_current_user` e gravação no `logout`**

Em `backend/app/services/auth.py`:
Em `get_current_user`:
Calcular `token_hash = hashlib.sha256(credentials.credentials.encode("ascii")).hexdigest()`.
Checar `if is_token_revoked(token_hash): raise authentication_error()`.

Em `backend/app/routes/auth.py`:
Em `logout`:
Extrair o token de `credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)`.
Decodificar payload para obter `exp`, calcular `token_hash` e chamar `revoke_token(token_hash, datetime.fromtimestamp(exp, timezone.utc))`.

- [ ] **Passo 4: Executar o teste para verificar aprovação**

Comando: `pytest backend/tests/test_auth_logout_revocation.py -q`
Esperado: PASS

- [ ] **Passo 5: Commit**

```bash
git add backend/app/services/auth.py backend/app/routes/auth.py backend/tests/test_auth_logout_revocation.py
git commit -m "feat(auth): enforce immediate token invalidation upon logout"
```

---

### Tarefa 7: Motor de Risco de Login com Janela Deslizante e Rate Limiting

**Arquivos:**
- Criar: `backend/app/services/risk_engine.py`
- Modificar: `backend/app/routes/auth.py:25-60`
- Testar: `backend/tests/test_risk_engine.py`
- Testar: `backend/tests/test_auth_risk_login.py`

**Interfaces:**
- Produz:
  - `LoginRiskEngine.inspect_client(ip: str, fingerprint: str) -> tuple[bool, int, int]`
  - `LoginRiskEngine.record_attempt(ip: str, fingerprint: str, email: str, success: bool, user_exists: bool) -> int`
- Consome: `request_ip(request)`

- [ ] **Passo 1: Escrever testes unitários para `LoginRiskEngine`**

Criar `backend/tests/test_risk_engine.py`:
```python
from app.services.risk_engine import LoginRiskEngine


def test_risk_engine_accumulates_score_and_blocks():
    engine = LoginRiskEngine()
    ip = "198.51.100.1"
    fp = "device-fingerprint-1"

    is_blocked, score, _ = engine.inspect_client(ip, fp)
    assert not is_blocked
    assert score == 0

    for _ in range(5):
        engine.record_attempt(ip=ip, fingerprint=fp, email="admin@example.com", success=False, user_exists=True)

    is_blocked, score, retry_after = engine.inspect_client(ip, fp)
    assert is_blocked
    assert score >= 100
    assert retry_after > 0


def test_risk_engine_detects_credential_stuffing_multiple_emails():
    engine = LoginRiskEngine()
    ip = "198.51.100.2"
    fp = "device-fingerprint-2"

    for i in range(5):
        engine.record_attempt(ip=ip, fingerprint=fp, email=f"user{i}@example.com", success=False, user_exists=False)

    is_blocked, score, _ = engine.inspect_client(ip, fp)
    assert is_blocked
    assert score >= 100
```

- [ ] **Passo 2: Implementar `LoginRiskEngine`**

Criar `backend/app/services/risk_engine.py`:
- Dataclass `AttemptRecord(timestamp, email, success, user_exists)`
- Classe `LoginRiskEngine`:
  - Thread-safe com `threading.Lock()`
  - Janela deslizante: 3600 segundos (1 hora)
  - Pontuações: +20 por falha consecutiva, +35 por rajada (> 3 em 10s), +30 para >= 3 emails distintos, +50 para >= 5 emails distintos, +15 para email inexistente.
  - Limiar: >= 100 bloqueia a chave por 900 segundos (15 minutos).
  - Singleton `get_risk_engine()`.

- [ ] **Passo 3: Integrar `LoginRiskEngine` em `backend/app/routes/auth.py`**

Em `backend/app/routes/auth.py` na rota `login`:
1. Verificar `is_blocked, score, retry_after = risk_engine.inspect_client(ip, fingerprint)`.
2. Se `is_blocked`:
   - Gravar log de auditoria `auth.login_blocked_risk`.
   - Lançar `HTTPException(status_code=429, detail="Too many attempts. Account locked temporarily.", headers={"Retry-After": str(retry_after)})`.
3. Se credenciais válidas:
   - `risk_engine.record_attempt(..., success=True)`.
4. Se credenciais inválidas:
   - `risk_engine.record_attempt(..., success=False, user_exists=(user is not None))`.

- [ ] **Passo 4: Executar testes unitários e de integração**

Criar `backend/tests/test_auth_risk_login.py`:
Testar que 5 logins inválidos vindos do mesmo IP disparam HTTP 429 na tentativa subsequente com cabeçalho `Retry-After`.
Comando:
```bash
pytest backend/tests/test_risk_engine.py backend/tests/test_auth_risk_login.py -q
```
Esperado: PASS

- [ ] **Passo 5: Commit**

```bash
git add backend/app/services/risk_engine.py backend/app/routes/auth.py backend/tests/test_risk_engine.py backend/tests/test_auth_risk_login.py
git commit -m "feat(auth): implement risk score engine and HTTP 429 brute force blocking"
```

---

### Tarefa 8: Defesa em Profundidade no Nginx e Suíte Completa de Verificação

**Arquivos:**
- Modificar: `infra/nginx/nginx.conf.template`
- Verificação: rodar todos os testes de backend, lint e build.

**Interfaces:**
- Nginx `limit_req_zone` para `/api/backend/api/v1/auth/login`.

- [ ] **Passo 1: Adicionar rate limiting de login no Nginx**

Em `infra/nginx/nginx.conf.template`:
Definir zona:
```nginx
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=10r/m;
```
Aplicar dentro de `location = /api/backend/api/v1/auth/login` com burst 5 nodelay.

- [ ] **Passo 2: Executar suíte completa de testes de backend**

Comando: `pytest backend/tests -q`
Esperado: 100% PASS com 0 falhas ou erros.

- [ ] **Passo 3: Executar build do frontend**

Comando: `cd frontend/dashboard && npm run build`
Esperado: Build concluído com sucesso.

- [ ] **Passo 4: Commit**

```bash
git add infra/nginx/nginx.conf.template
git commit -m "feat(nginx): add defense-in-depth rate limiting zone for login route"
```
