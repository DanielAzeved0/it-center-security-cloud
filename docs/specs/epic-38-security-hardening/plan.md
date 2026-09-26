# EPIC 38: Security Hardening & Login Risk Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement comprehensive security hardening across the IT Center Security Cloud platform: a risk-based login rate limiting engine with HTTP 429 blocking, real token revocation on logout via PostgreSQL, strict production secret length validation, XML escaping in ReportLab PDF generation, strict regex validation for `rustdesk_id` on both ends, and payload/header hardening on the Next.js proxy.

**Architecture:** A lightweight in-memory sliding-window risk engine (`LoginRiskEngine`) evaluates client IP, device fingerprint, burst velocity, and credential-stuffing patterns without overloading PostgreSQL. Exceeded thresholds trigger an immediate HTTP 429 response. Token revocation persists token SHA-256 hashes in an idempotent `revoked_tokens` PostgreSQL table checked at `get_current_user`. All dynamic inputs into ReportLab `Paragraph()` are escaped with `xml.sax.saxutils.escape`. Next.js proxy validates `Content-Type` and enforces a 1MB payload ceiling while forwarding `X-Real-IP` and `User-Agent`.

**Tech Stack:** Python 3.13, FastAPI, PostgreSQL (psycopg 3 raw SQL), Next.js 16 (App Router / TypeScript), ReportLab, Nginx.

**Spec:** [`docs/specs/epic-38-security-hardening/spec.md`](file:///C:/Users/gizad/it-center-security-cloud/docs/specs/epic-38-security-hardening/spec.md)

## Global Constraints

- No external caching/message queuing servers (no Redis, Memcached, RabbitMQ) — runs fully contained in Python memory + PostgreSQL on the 1GB RAM VM.
- All PostgreSQL operations use raw `psycopg` queries; no ORM.
- Zero breaking changes to existing agent check-in routes or existing user session tokens.
- Strict TDD: tests written and confirmed failing before writing minimal implementation.

---

### Task 1: Secret Length Validation in Production Configuration

**Files:**
- Modify: `backend/app/core/config.py:19-38`
- Test: `backend/tests/test_config.py`

**Interfaces:**
- Consumes: `Settings.validate_runtime_configuration()`
- Produces: `RuntimeError` if `AUTH_TOKEN_SECRET` or `AGENT_API_KEY` has length < 32 in `app_env == "production"`.

- [ ] **Step 1: Write the failing test**

Create/update `backend/tests/test_config.py`:
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

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_config.py -q`
Expected: FAIL with `Failed: DID NOT RAISE <class 'RuntimeError'>`

- [ ] **Step 3: Implement secret length validation**

Modify `backend/app/core/config.py`:
```python
        if self.agent_api_key in insecure_values or len(self.agent_api_key or "") < 32:
            raise RuntimeError("AGENT_API_KEY must be configured with a non-default value of at least 32 characters in production")

        if self.auth_token_secret in insecure_values or len(self.auth_token_secret or "") < 32:
            raise RuntimeError("AUTH_TOKEN_SECRET must be configured with a non-default value of at least 32 characters in production")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_config.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/config.py backend/tests/test_config.py
git commit -m "feat(security): enforce minimum 32 chars for production secrets in config"
```

---

### Task 2: XML Escaping for Dynamic Values in ReportLab PDF Generation

**Files:**
- Modify: `backend/app/services/reports.py:114-140`
- Test: `backend/tests/test_reports.py`

**Interfaces:**
- Consumes: `xml.sax.saxutils.escape`
- Produces: Sanitized `Paragraph` elements in `build_machine_report_pdf` that never raise `ValueError` on XML entities or tags.

- [ ] **Step 1: Write the failing test**

In `backend/tests/test_reports.py`:
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
    # Should build PDF without XML parsing errors
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

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_reports.py::test_build_machine_report_pdf_escapes_xml_tags_in_hostname -q`
Expected: FAIL or raise XML parsing exception from ReportLab.

- [ ] **Step 3: Implement escaping in reports.py**

Modify `backend/app/services/reports.py`:
Import `from xml.sax.saxutils import escape as xml_escape`.
In `build_machine_report_pdf`:
Escape `machine.hostname`, `machine.username`, and any dynamic string passed to `Paragraph(...)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_reports.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/reports.py backend/tests/test_reports.py
git commit -m "fix(reports): escape dynamic text in ReportLab Paragraph elements"
```

---

### Task 3: Backend Schema Pattern & Frontend Sanitization for `rustdesk_id`

**Files:**
- Modify: `backend/app/schemas/machine.py:45-48`
- Modify: `frontend/dashboard/components/MachineDetailView.tsx:300-320`
- Test: `backend/tests/test_machine_schemas.py`
- Test: `frontend/dashboard/__tests__/rustdesk_validation.test.ts`

**Interfaces:**
- Consumes: Pydantic `Field(pattern=r"^\d{5,12}$")`
- Produces: Validated `rustdesk_id` in `MachineRustdeskUpdate`; safe URI `rustdesk://connect?id=...` in UI.

- [ ] **Step 1: Write the failing backend test**

Create `backend/tests/test_machine_schemas.py`:
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
        MachineRustdeskUpdate(rustdesk_id="123")  # too short (< 5)

    with pytest.raises(ValidationError):
        MachineRustdeskUpdate(rustdesk_id="1234567890123")  # too long (> 12)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_machine_schemas.py -q`
Expected: FAIL

- [ ] **Step 3: Update schema and frontend**

In `backend/app/schemas/machine.py`:
```python
class MachineRustdeskUpdate(BaseModel):
    rustdesk_id: str | None = Field(default=None, pattern=r"^\d{5,12}$")
```

In `frontend/dashboard/components/MachineDetailView.tsx`:
Add regex guard:
```tsx
const isValidRustdeskId = detail.rustdesk_id ? /^\d{5,12}$/.test(detail.rustdesk_id) : false;
```
Render active connect link only if `isValidRustdeskId && canManageRustdesk`, and encode:
```tsx
href={`rustdesk://connect?id=${encodeURIComponent(detail.rustdesk_id)}`}
```

- [ ] **Step 4: Run backend tests**

Run: `pytest backend/tests/test_machine_schemas.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/machine.py backend/tests/test_machine_schemas.py frontend/dashboard/components/MachineDetailView.tsx
git commit -m "feat(security): enforce numeric format for rustdesk_id on backend and frontend"
```

---

### Task 4: Next.js Proxy Hardening & Env Cleanup

**Files:**
- Modify: `frontend/dashboard/app/api/backend/[...path]/route.ts:90-110, 175-200`
- Modify: `infra/docker-compose.production.yml`
- Modify: `infra/docker-compose.yml`
- Modify: `.env.example`
- Modify: `.env.production.example`

**Interfaces:**
- Consumes: Next.js Request headers
- Produces: Proxied requests carrying `X-Real-IP` and `User-Agent`; rejects >1MB with 413, invalid Content-Type with 415.

- [ ] **Step 1: Implement proxy payload size and Content-Type checks**

In `frontend/dashboard/app/api/backend/[...path]/route.ts`:
In `fetchUpstream`:
Add forwarding for `X-Real-IP` and `User-Agent`:
```ts
    headers: {
      "Content-Type": request.headers.get("Content-Type") ?? "application/json",
      "X-Real-IP": request.headers.get("x-real-ip") ?? request.headers.get("x-forwarded-for")?.split(",")[0].trim() ?? "127.0.0.1",
      "User-Agent": request.headers.get("user-agent") ?? "itcenter-dashboard",
      ...(sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {}),
    },
```
In `proxyRequest`:
Before reading body:
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

- [ ] **Step 2: Clean up obsolete `NEXT_PUBLIC_API_BASE_URL`**

Remove `NEXT_PUBLIC_API_BASE_URL` from:
- `infra/docker-compose.production.yml`
- `infra/docker-compose.yml`
- `.env.example`
- `.env.production.example`

- [ ] **Step 3: Run compose config check**

Run: `docker compose -f infra/docker-compose.yml config -q`
Expected: PASS (exit code 0)

- [ ] **Step 4: Commit**

```bash
git add frontend/dashboard/app/api/backend/[...path]/route.ts infra/docker-compose.production.yml infra/docker-compose.yml .env.example .env.production.example
git commit -m "feat(proxy): harden request proxying with size and content-type validation and header forwarding"
```

---

### Task 5: Migration 014 & Revoked Tokens Repository

**Files:**
- Create: `backend/migrations/014_create_revoked_tokens.sql`
- Create: `backend/app/repositories/revoked_tokens.py`
- Test: `backend/tests/test_revoked_tokens_repo.py`

**Interfaces:**
- Produces:
  - `revoke_token(token_hash: str, expires_at: datetime) -> None`
  - `is_token_revoked(token_hash: str) -> bool`
  - `purge_expired_revoked_tokens() -> int`

- [ ] **Step 1: Write migration `014`**

Create `backend/migrations/014_create_revoked_tokens.sql`:
```sql
CREATE TABLE IF NOT EXISTS revoked_tokens (
    token_hash VARCHAR(64) PRIMARY KEY,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_revoked_tokens_expires_at ON revoked_tokens (expires_at);
```

- [ ] **Step 2: Write repository tests**

Create `backend/tests/test_revoked_tokens_repo.py`:
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

- [ ] **Step 3: Implement `backend/app/repositories/revoked_tokens.py`**

Implement `revoke_token`, `is_token_revoked` (with ON CONFLICT DO NOTHING), and `purge_expired_revoked_tokens` using `get_connection()`.

- [ ] **Step 4: Run migration and test repository**

Run:
```bash
python backend/apply_migrations.py
pytest backend/tests/test_revoked_tokens_repo.py -q
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/migrations/014_create_revoked_tokens.sql backend/app/repositories/revoked_tokens.py backend/tests/test_revoked_tokens_repo.py
git commit -m "feat(auth): create revoked_tokens table and repository"
```

---

### Task 6: Token Revocation in Auth Service and Logout Endpoint

**Files:**
- Modify: `backend/app/services/auth.py:125-145`
- Modify: `backend/app/routes/auth.py:85-99`
- Test: `backend/tests/test_auth_logout_revocation.py`

**Interfaces:**
- Consumes: `revoke_token`, `is_token_revoked`
- Produces: `get_current_user` checking revocation; `POST /logout` revoking the caller's active bearer token.

- [ ] **Step 1: Write failing integration test for logout token revocation**

Create `backend/tests/test_auth_logout_revocation.py`:
```python
def test_logout_revokes_token_immediately(client, auth_headers):
    # auth_headers gives a valid token
    me_resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_resp.status_code == 200

    logout_resp = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert logout_resp.status_code == 200

    # Same token must now be rejected
    second_me = client.get("/api/v1/auth/me", headers=auth_headers)
    assert second_me.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_auth_logout_revocation.py -q`
Expected: FAIL (second_me returns 200 instead of 401)

- [ ] **Step 3: Implement revocation check in `get_current_user` and record in `logout`**

In `backend/app/services/auth.py`:
In `get_current_user`:
Compute `token_hash = hashlib.sha256(credentials.credentials.encode("ascii")).hexdigest()`.
Check `if is_token_revoked(token_hash): raise authentication_error()`.

In `backend/app/routes/auth.py`:
In `logout`:
Extract token from `credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)`.
Decode payload to get `exp`, compute `token_hash`, and call `revoke_token(token_hash, datetime.fromtimestamp(exp, timezone.utc))`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_auth_logout_revocation.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/auth.py backend/app/routes/auth.py backend/tests/test_auth_logout_revocation.py
git commit -m "feat(auth): enforce immediate token invalidation upon logout"
```

---

### Task 7: Login Risk Engine with Sliding Window & Rate Limiting

**Files:**
- Create: `backend/app/services/risk_engine.py`
- Modify: `backend/app/routes/auth.py:25-60`
- Test: `backend/tests/test_risk_engine.py`
- Test: `backend/tests/test_auth_risk_login.py`

**Interfaces:**
- Produces:
  - `LoginRiskEngine.inspect_client(ip: str, fingerprint: str) -> tuple[bool, int, int]`
  - `LoginRiskEngine.record_attempt(ip: str, fingerprint: str, email: str, success: bool, user_exists: bool) -> int`
- Consumes: `request_ip(request)`

- [ ] **Step 1: Write unit tests for `LoginRiskEngine`**

Create `backend/tests/test_risk_engine.py`:
```python
from app.services.risk_engine import LoginRiskEngine


def test_risk_engine_accumulates_score_and_blocks():
    engine = LoginRiskEngine()
    ip = "198.51.100.1"
    fp = "device-fingerprint-1"

    # Initial state
    is_blocked, score, _ = engine.inspect_client(ip, fp)
    assert not is_blocked
    assert score == 0

    # Record 5 consecutive failed attempts
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

- [ ] **Step 2: Implement `LoginRiskEngine`**

Create `backend/app/services/risk_engine.py`:
- Dataclass `AttemptRecord(timestamp, email, success, user_exists)`
- Class `LoginRiskEngine`:
  - Thread-safe with `threading.Lock()`
  - Sliding window: 3600 seconds (1 hour)
  - Scores: +20 consecutive failure, +35 burst (>3 in 10s), +30 for >=3 distinct emails, +50 for >=5 distinct emails, +15 for non-existing email.
  - Threshold: >= 100 blocks key for 900 seconds (15 min).
  - Singleton `get_risk_engine()`.

- [ ] **Step 3: Integrate `LoginRiskEngine` into `backend/app/routes/auth.py`**

In `backend/app/routes/auth.py` `login`:
1. Check `is_blocked, score, retry_after = risk_engine.inspect_client(ip, fingerprint)`.
2. If `is_blocked`:
   - Log audit `auth.login_blocked_risk`.
   - Raise `HTTPException(status_code=429, detail="Too many attempts. Account locked temporarily.", headers={"Retry-After": str(retry_after)})`.
3. If credentials valid:
   - `risk_engine.record_attempt(..., success=True)`.
4. If credentials invalid:
   - `risk_engine.record_attempt(..., success=False, user_exists=(user is not None))`.

- [ ] **Step 4: Run unit and integration tests**

Create `backend/tests/test_auth_risk_login.py`:
Test that 5 invalid logins from same IP trigger HTTP 429 on the 6th attempt with header `Retry-After`.
Run:
```bash
pytest backend/tests/test_risk_engine.py backend/tests/test_auth_risk_login.py -q
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/risk_engine.py backend/app/routes/auth.py backend/tests/test_risk_engine.py backend/tests/test_auth_risk_login.py
git commit -m "feat(auth): implement risk score engine and HTTP 429 brute force blocking"
```

---

### Task 8: Nginx Defense-in-Depth & Full Verification Suite

**Files:**
- Modify: `infra/nginx/nginx.conf.template`
- Verification: run all backend tests, lint, and build.

**Interfaces:**
- Nginx `limit_req_zone` for `/api/backend/api/v1/auth/login`.

- [ ] **Step 1: Add login rate limiting in Nginx**

In `infra/nginx/nginx.conf.template`:
Define zone:
```nginx
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=10r/m;
```
Apply inside `location = /api/backend/api/v1/auth/login` with burst 5 nodelay.

- [ ] **Step 2: Run full backend test suite**

Run: `pytest backend/tests -q`
Expected: 100% PASS with 0 failures or errors.

- [ ] **Step 3: Run frontend build**

Run: `cd frontend/dashboard && npm run build`
Expected: Successful build.

- [ ] **Step 4: Commit**

```bash
git add infra/nginx/nginx.conf.template
git commit -m "feat(nginx): add defense-in-depth rate limiting zone for login route"
```
