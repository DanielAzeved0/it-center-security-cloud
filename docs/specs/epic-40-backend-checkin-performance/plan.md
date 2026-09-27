# Implementation Plan: EPIC 40 - Desempenho do Backend no Check-in

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Otimizar o desempenho do backend FastAPI eliminando a abertura excessiva de conexões TCP através de connection pool (`psycopg_pool`), throttlando a varredura global de offline e aplicando batching/fingerprinting em gravações do check-in.

**Architecture:** Substituição da conexão raw por `psycopg_pool.ConnectionPool` (1-5 conexões) transparente em `app.database`, throttle em memória de 30s para `mark_stale_machines_offline(machine_id=None)`, coluna `installed_programs_hash` na tabela `machines` (migration 015) para evitar DELETE+INSERT de centenas de registros sem alteração, e persistência em lote via `cursor.executemany` para eventos USB e administradores locais.

**Tech Stack:** Python 3.13, FastAPI, PostgreSQL 16, psycopg 3.2.x, psycopg-pool 3.2.x, pytest.

**Spec:** `docs/specs/epic-40-backend-checkin-performance/spec.md`

## Global Constraints

- O driver de banco de dados deve permanecer `psycopg` puro com `psycopg_pool` (zero ORM, zero SQLAlchemy).
- A assinatura e uso de `get_connection()` como context manager (`with get_connection() as conn:`) deve ser 100% mantida para todos os repositórios existentes.
- O connection pool deve ser configurado com `min_size=1`, `max_size=5`, `timeout=10.0` para operar com segurança na VM de 954MB.
- A migration `015_add_installed_programs_hash.sql` deve ser idempotente (`ADD COLUMN IF NOT EXISTS`).
- Todos os testes no Windows devem rodar via `.venv\Scripts\python.exe -m pytest`.

---

### Task 1: Connection Pool com `psycopg_pool` em `database.py`

**Files:**
- Modify: `backend/requirements.txt:5`
- Modify: `backend/app/database.py:1-22`
- Test: `backend/tests/test_database_pool.py`

**Interfaces:**
- Consumes: `get_database_url()` de `app.database`.
- Produces: `get_connection()` (contextmanager gerando conexão do pool), `get_connection_pool() -> ConnectionPool`, `close_connection_pool() -> None`.

- [ ] **Step 1: Instalar dependência e atualizar requirements.txt**

Adicionar `psycopg-pool>=3.2.0` em `backend/requirements.txt` e instalar no ambiente virtual:
```bash
uv pip install "psycopg-pool>=3.2.0" --python .venv\Scripts\python.exe
```

- [ ] **Step 2: Escrever o teste que falha para o Connection Pool**

Criar `backend/tests/test_database_pool.py`:
```python
from app.database import close_connection_pool, get_connection, get_connection_pool


def test_connection_pool_reuses_connections():
    close_connection_pool()
    pool = get_connection_pool()
    assert pool.min_size == 1
    assert pool.max_size == 5

    with get_connection() as conn1:
        row1 = conn1.execute("SELECT 1 AS alive").fetchone()
        assert row1["alive"] == 1

    with get_connection() as conn2:
        row2 = conn2.execute("SELECT 2 AS alive").fetchone()
        assert row2["alive"] == 2

    # Verifica que o pool continua ativo e funcional
    assert pool.get_stats()["pool_available"] >= 1
    close_connection_pool()
```

- [ ] **Step 3: Executar o teste para verificar falha**

Run: `.venv\Scripts\python.exe -m pytest backend/tests/test_database_pool.py -v`
Expected: FAIL (funções `get_connection_pool` ou `close_connection_pool` inexistentes).

- [ ] **Step 4: Implementar o ConnectionPool em `backend/app/database.py`**

Modificar `backend/app/database.py`:
```python
import os
import threading
from contextlib import contextmanager

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

DEFAULT_DATABASE_URL = "postgresql://itcenter:change-me@127.0.0.1:5432/it_center_security_cloud"

_pool: ConnectionPool | None = None
_pool_lock = threading.Lock()


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    if os.getenv("APP_ENV", "development").lower() == "production":
        raise RuntimeError("DATABASE_URL must be configured in production")

    return DEFAULT_DATABASE_URL


def get_connection_pool() -> ConnectionPool:
    global _pool
    if _pool is None or _pool.closed:
        with _pool_lock:
            if _pool is None or _pool.closed:
                _pool = ConnectionPool(
                    conninfo=get_database_url(),
                    min_size=1,
                    max_size=5,
                    timeout=10.0,
                    max_idle=300.0,
                    kwargs={"row_factory": dict_row},
                    open=True,
                )
    return _pool


def close_connection_pool() -> None:
    global _pool
    with _pool_lock:
        if _pool is not None and not _pool.closed:
            _pool.close()
            _pool = None


@contextmanager
def get_connection():
    pool = get_connection_pool()
    with pool.connection() as connection:
        yield connection
```

- [ ] **Step 5: Executar o teste para verificar sucesso**

Run: `.venv\Scripts\python.exe -m pytest backend/tests/test_database_pool.py -v`
Expected: PASS

- [ ] **Step 6: Executar regressão do banco de dados**

Run: `.venv\Scripts\python.exe -m pytest backend/tests/test_database.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/requirements.txt backend/app/database.py backend/tests/test_database_pool.py
git commit -m "feat(database): implement connection pooling with psycopg-pool"
```

---

### Task 2: Throttle de 30s em `mark_stale_machines_offline`

**Files:**
- Modify: `backend/app/repositories/machines.py:319-366`
- Test: `backend/tests/test_machines_throttle.py`

**Interfaces:**
- Consumes: `mark_stale_machines_offline(machine_id: int | None = None)` em `app.repositories.machines`.
- Produces: `reset_stale_throttle_for_testing() -> None`.

- [ ] **Step 1: Escrever teste de throttle**

Criar `backend/tests/test_machines_throttle.py`:
```python
import time
from unittest.mock import patch

from app.repositories.machines import mark_stale_machines_offline, reset_stale_throttle_for_testing


def test_mark_stale_machines_offline_throttled_for_global_calls():
    reset_stale_throttle_for_testing()

    with patch("app.repositories.machines.get_connection") as mock_conn:
        # Primeira chamada global: deve executar
        mark_stale_machines_offline(machine_id=None)
        assert mock_conn.call_count == 1

        # Segunda chamada global imediata: deve ser ignorada pelo throttle
        mark_stale_machines_offline(machine_id=None)
        assert mock_conn.call_count == 1

        # Chamada específica para machine_id: nunca sofre throttle
        mark_stale_machines_offline(machine_id=99)
        assert mock_conn.call_count == 2
```

- [ ] **Step 2: Executar teste para verificar falha**

Run: `.venv\Scripts\python.exe -m pytest backend/tests/test_machines_throttle.py -v`
Expected: FAIL (`reset_stale_throttle_for_testing` não existe ou contagem de mock não bate).

- [ ] **Step 3: Implementar throttle em `backend/app/repositories/machines.py`**

Adicionar controle de tempo e lock em `backend/app/repositories/machines.py`:
```python
_last_global_stale_sweep: float = 0.0
_stale_sweep_lock = threading.Lock()
STALE_THROTTLE_SECONDS = 30.0


def reset_stale_throttle_for_testing() -> None:
    global _last_global_stale_sweep
    with _stale_sweep_lock:
        _last_global_stale_sweep = 0.0


def mark_stale_machines_offline(machine_id: int | None = None) -> None:
    global _last_global_stale_sweep

    if machine_id is None:
        now = time.time()
        with _stale_sweep_lock:
            if now - _last_global_stale_sweep < STALE_THROTTLE_SECONDS:
                return
            _last_global_stale_sweep = now
    # restante da função inalterado...
```

- [ ] **Step 4: Executar o teste para verificar sucesso**

Run: `.venv\Scripts\python.exe -m pytest backend/tests/test_machines_throttle.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/repositories/machines.py backend/tests/test_machines_throttle.py
git commit -m "perf(machines): throttle global mark_stale_machines_offline calls"
```

---

### Task 3: Fingerprint de Programas Instalados (Migration 015 e `machines.py`)

**Files:**
- Create: `backend/migrations/015_add_installed_programs_hash.sql`
- Modify: `backend/app/repositories/machines.py:115-144`
- Test: `backend/tests/test_installed_programs_fingerprint.py`

**Interfaces:**
- Consumes: `AgentCheckinRequest.installed_programs`
- Produces: `machines.installed_programs_hash` persistido e comparado para saltar DELETE/INSERT redundante.

- [ ] **Step 1: Criar migration 015**

Criar `backend/migrations/015_add_installed_programs_hash.sql`:
```sql
ALTER TABLE machines
ADD COLUMN IF NOT EXISTS installed_programs_hash VARCHAR(64);
```

- [ ] **Step 2: Aplicar migration localmente**

Run: `.venv\Scripts\python.exe backend/apply_migrations.py`
Expected: "Applied 15 migration file(s)."

- [ ] **Step 3: Escrever teste de fingerprint de programas**

Criar `backend/tests/test_installed_programs_fingerprint.py`:
```python
from app.repositories.machines import compute_installed_programs_hash, save_machine_checkin
from app.schemas.agent import AgentCheckinRequest, InstalledProgramPayload


def test_compute_installed_programs_hash_deterministic():
    p1 = [InstalledProgramPayload(name="App A", version="1.0", publisher="Pub A"), InstalledProgramPayload(name="App B", version="2.0", publisher="Pub B")]
    p2 = [InstalledProgramPayload(name="App B", version="2.0", publisher="Pub B"), InstalledProgramPayload(name="App A", version="1.0", publisher="Pub A")]
    assert compute_installed_programs_hash(p1) == compute_installed_programs_hash(p2)


def test_save_machine_checkin_skips_unchanged_installed_programs(clean_db):
    programs = [InstalledProgramPayload(name="App 1", version="1.0", publisher="Pub 1")]
    payload1 = AgentCheckinRequest(
        hostname="FP-TEST-01",
        ip_address="10.0.0.1",
        mac_address="00:11:22:33:44:55",
        os_version="Windows 11",
        installed_programs=programs,
    )

    summary1, _ = save_machine_checkin(payload1)
    
    # Salvar segundo checkin identico
    summary2, _ = save_machine_checkin(payload1)
    assert summary1.id == summary2.id

    from app.database import get_connection
    with get_connection() as conn:
        row = conn.execute("SELECT installed_programs_hash FROM machines WHERE id = %s", (summary1.id,)).fetchone()
        assert row["installed_programs_hash"] is not None
        assert row["installed_programs_hash"] == compute_installed_programs_hash(programs)
```

- [ ] **Step 4: Executar teste para verificar falha**

Run: `.venv\Scripts\python.exe -m pytest backend/tests/test_installed_programs_fingerprint.py -v`
Expected: FAIL (`compute_installed_programs_hash` não existe).

- [ ] **Step 5: Implementar fingerprinting em `backend/app/repositories/machines.py`**

Em `backend/app/repositories/machines.py`:
1. Criar helper `compute_installed_programs_hash(programs: list[InstalledProgramPayload]) -> str`:
```python
def compute_installed_programs_hash(programs: list[InstalledProgramPayload]) -> str:
    normalized = sorted(
        (p.name.strip().lower(), (p.version or "").strip(), (p.publisher or "").strip())
        for p in programs
    )
    raw = json.dumps(normalized, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
```
2. No `save_machine_checkin`, comparar `current_hash` com `machine_row.get("installed_programs_hash")`:
   Se diferente:
   - Executar `DELETE FROM installed_programs WHERE machine_id = %s`
   - Executar `cursor.executemany(...)`
   - `UPDATE machines SET installed_programs_hash = %s WHERE id = %s`
   Se igual:
   - Pular o DELETE e o executemany completamente.

- [ ] **Step 6: Executar teste para verificar sucesso**

Run: `.venv\Scripts\python.exe -m pytest backend/tests/test_installed_programs_fingerprint.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/migrations/015_add_installed_programs_hash.sql backend/app/repositories/machines.py backend/tests/test_installed_programs_fingerprint.py
git commit -m "feat(machines): avoid rewriting installed programs when fingerprint matches"
```

---

### Task 4: Inserção em Lote de Eventos USB

**Files:**
- Modify: `backend/app/repositories/security_events.py`
- Modify: `backend/app/services/agent.py:148-158`
- Test: `backend/tests/test_batch_usb_events.py`

**Interfaces:**
- Produces: `create_security_events_batch(events: list[dict]) -> None` em `app.repositories.security_events`.
- Consumes: Chamado por `process_usb_devices` em `app.services.agent`.

- [ ] **Step 1: Escrever teste para inserção em lote de eventos USB**

Criar `backend/tests/test_batch_usb_events.py`:
```python
from app.repositories.security_events import create_security_events_batch, list_security_events
from app.repositories.machines import save_machine_checkin
from app.schemas.agent import AgentCheckinRequest
from app.services.agent import process_usb_devices


def test_process_usb_devices_batches_insert(clean_db):
    payload = AgentCheckinRequest(
        hostname="USB-BATCH-01",
        ip_address="10.0.0.2",
        mac_address="00:11:22:33:44:66",
        os_version="Windows 11",
        security={"usb_devices": [{"name": "Kingston DT"}, {"name": "SanDisk Ultra"}]}
    )
    summary, _ = save_machine_checkin(payload)
    process_usb_devices(payload, summary.id)

    events = list_security_events(limit=10)
    usb_events = [e for e in events if e.event_type == "usb_detected" and e.machine_id == summary.id]
    assert len(usb_events) == 2
```

- [ ] **Step 2: Executar teste para verificar falha**

Run: `.venv\Scripts\python.exe -m pytest backend/tests/test_batch_usb_events.py -v`
Expected: FAIL (`create_security_events_batch` não definido).

- [ ] **Step 3: Implementar `create_security_events_batch` em `backend/app/repositories/security_events.py`**

Adicionar em `backend/app/repositories/security_events.py`:
```python
def create_security_events_batch(events: list[dict]) -> None:
    if not events:
        return

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO security_events (
                    machine_id,
                    event_type,
                    severity,
                    source,
                    description,
                    raw_data
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        e["machine_id"],
                        e["event_type"],
                        e["severity"],
                        e["source"],
                        e["description"],
                        Jsonb(e["raw_data"]),
                    )
                    for e in events
                ],
            )
```

- [ ] **Step 4: Atualizar `process_usb_devices` em `backend/app/services/agent.py`**

```python
def process_usb_devices(payload: AgentCheckinRequest, machine_id: int) -> None:
    events = [
        {
            "machine_id": machine_id,
            "event_type": "usb_detected",
            "severity": "low",
            "source": "agent",
            "description": f"Dispositivo USB detectado na maquina {_hostname(payload)}: {str(device.get('name') or 'USB device')}.",
            "raw_data": device,
        }
        for device in payload.security.usb_devices
    ]
    if events:
        create_security_events_batch(events)
```

- [ ] **Step 5: Executar teste para verificar sucesso**

Run: `.venv\Scripts\python.exe -m pytest backend/tests/test_batch_usb_events.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/repositories/security_events.py backend/app/services/agent.py backend/tests/test_batch_usb_events.py
git commit -m "perf(agent): batch USB security events creation using executemany"
```

---

### Task 5: Inserção em Lote de Administradores Locais em `local_admins.py`

**Files:**
- Modify: `backend/app/repositories/local_admins.py:31-45`
- Test: `backend/tests/test_batch_local_admins.py`

**Interfaces:**
- Consumes: `sync_machine_local_admins(machine_id: int, admin_names: list[str]) -> list[str]`

- [ ] **Step 1: Escrever teste para inserção em lote de admins locais**

Criar `backend/tests/test_batch_local_admins.py`:
```python
from app.repositories.local_admins import sync_machine_local_admins
from app.repositories.machines import save_machine_checkin
from app.schemas.agent import AgentCheckinRequest


def test_sync_machine_local_admins_batches(clean_db):
    payload = AgentCheckinRequest(
        hostname="ADMIN-BATCH-01",
        ip_address="10.0.0.3",
        mac_address="00:11:22:33:44:77",
        os_version="Windows 11",
    )
    summary, _ = save_machine_checkin(payload)

    # Primeira sincronização com múltiplos admins
    admins = ["Administrator", "SecOps", "Support"]
    new_admins = sync_machine_local_admins(summary.id, admins)
    # Na primeira vez que a máquina cadastra admins, existing_rows era vazio, retorna []
    assert new_admins == []

    # Segunda sincronização adicionando novo admin
    admins.append("Auditor")
    new_detected = sync_machine_local_admins(summary.id, admins)
    assert new_detected == ["Auditor"]
```

- [ ] **Step 2: Implementar executemany em `backend/app/repositories/local_admins.py`**

Substituir o loop sequencial por `cursor.executemany`:
```python
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO machine_local_admins (
                        machine_id,
                        admin_name,
                        last_seen_at
                    )
                    VALUES (%s, %s, now())
                    ON CONFLICT (machine_id, lower(admin_name))
                    DO UPDATE SET last_seen_at = now()
                    """,
                    [(machine_id, admin) for admin in normalized_admins],
                )
```

- [ ] **Step 3: Executar teste de admins locais**

Run: `.venv\Scripts\python.exe -m pytest backend/tests/test_batch_local_admins.py -v`
Expected: PASS

- [ ] **Step 4: Executar regressão completa de testes do backend**

Run: `.venv\Scripts\python.exe -m pytest backend/tests/ -q`
Expected: All 180+ tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/repositories/local_admins.py backend/tests/test_batch_local_admins.py
git commit -m "perf(local_admins): use executemany for batch upsert of local admins"
```
