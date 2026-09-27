# Spec: EPIC 40 - Desempenho do Backend no Check-in (2026-09-26)

## Metadata

- Status: SPECIFIED
- Nivel de rigor: 3 (arquitetural) — altera camada central de conexao com banco de dados (`psycopg_pool`), schema do banco (migration 015), throttle de leitura e batching no fluxo critico de check-in.
- Autor/origem: Auditoria de qualidade de 2026-08-20 (`docs/development/TASKS.md`, EPIC 40) + decisoes de design da sessao 2026-09-26.
- Data: 2026-09-26
- Dependencias: psycopg 3, PostgreSQL 16, migration 014 (revoked_tokens).

---

## Context

O backend FastAPI opera atualmente abrindo uma nova conexao TCP isolada com o PostgreSQL a cada chamada de repositorio atraves de `psycopg.connect()`.
Um unico check-in de agente passa por `save_machine_checkin`, `process_security_posture`, processamento de eventos de USB, admins locais e alertas, abrindo facilmente entre 10 e 40 conexoes TCP brutas por ciclo. Cada conexao paga o custo de handshake de rede, autenticacao e alocacao de processo backend no PostgreSQL.
Alem disso:
1. `mark_stale_machines_offline()` e chamado sem throttle a cada requisicao de leitura do dashboard (`list_machines`, `get_machine`, `get_dashboard_summary`), disparando um `UPDATE` de varredura global sobre a tabela `machines` concorrentemente com leituras.
2. `installed_programs` e inteiramente apagado (`DELETE FROM installed_programs WHERE machine_id = ...`) e reinserido a cada 5 minutos por agente, gerando centenas de escritas desnecessarias em maquinas cujo inventario de software nao mudou.
3. Eventos de USB e administradores locais sao persistidos atraves de loops sequenciais com multiplas chamadas `execute()` individuais.

Em uma VM de 1GB de RAM (Oracle Cloud Free Tier) com recursos rigorosamente limitados, esse padrao e o principal gargalo de CPU e conexoes do sistema.

---

## Goal

Otimizar drasticamente o desempenho do backend e do fluxo de check-in sem introduzir ORM ou cache distribuido externo:
1. Implementar Connection Pooling no driver `psycopg` via `psycopg-pool` (`min_size=1`, `max_size=5`), preservando a assinatura e o comportamento transparente de context manager de `get_connection()`.
2. Implementar throttle em memoria de 30 segundos em `mark_stale_machines_offline()` para consultas globais disparadas por leituras do dashboard.
3. Adicionar coluna `installed_programs_hash VARCHAR(64)` na tabela `machines` (migration 015) para evitar regravacoes de programas instalados quando o hash SHA-256 da lista nao tiver sido alterado.
4. Agrupar em lote a criacao de eventos de seguranca USB via `executemany`.
5. Substituir o loop sequencial de insercao de administradores locais por `executemany`.

---

## Scope

- **Trilha 1: Connection Pool no Database Layer**
  - Adicionar `psycopg-pool>=3.2.0` em `backend/requirements.txt`.
  - Refatorar `backend/app/database.py` para instanciar `ConnectionPool` singleton com lazy initialization e encerramento gracioso via `close_connection_pool()`.
  - Garantir compatibilidade transparente para todos os repositorios e rotinas de migracao.
- **Trilha 2: Throttle de Máquinas Offline**
  - Modificar `backend/app/repositories/machines.py` para impor janela minima de 30s entre varreduras globais de `mark_stale_machines_offline(machine_id=None)`.
- **Trilha 3: Fingerprint de Programas Instalados**
  - Migration `backend/migrations/015_add_installed_programs_hash.sql`.
  - Calculo de hash deterministico em `save_machine_checkin` e desvio condicional de escrita.
- **Trilha 4: Batching de Eventos USB e Admins Locais**
  - `backend/app/repositories/security_events.py`: implementar `create_security_events_batch(events)`.
  - `backend/app/services/agent.py`: chamar criacao em lote para `process_usb_devices`.
  - `backend/app/repositories/local_admins.py`: converter loop para `cursor.executemany`.

---

## Out of Scope

- Introducao de Redis, Memcached ou message brokers externos.
- Troca do driver `psycopg` por SQLAlchemy ou bibliotecas assincronas.
- Modificacao do contrato da API de check-in do agente ou dos schemas JSON trocados com o dashboard.

---

## Functional Requirements

```
FR-001: Connection Pool Transparente
- get_connection() deve retornar conexoes ativas a partir de um pool ConnectionPool (min_size=1, max_size=5, timeout=10.0s).
- Ao sair do bloco 'with get_connection() as conn:', a conexao deve retornar ao pool de forma limpa.
- O pool deve ser encerrado no shutdown da aplicacao FastAPI e apoiar reinicializacao isolada em testes.

FR-002: Throttle de Varredura de Offline
- Quando mark_stale_machines_offline for chamado com machine_id=None, a varredura so deve executar caso tenham se passado >= 30 segundos desde a ultima varredura global.
- Quando mark_stale_machines_offline for chamado com machine_id especifico, a operacao deve executar imediatamente.

FR-003: Deteccao de Mudanca de Programas Instalados
- O check-in deve calcular o hash SHA-256 ordenado e normalizado de (name, version, publisher) da lista de programas.
- Se o hash gerado for identico ao valor armazenado na coluna machines.installed_programs_hash, nenhuma operacao de DELETE ou INSERT deve ser executada na tabela installed_programs.
- Se o hash for diferente ou nulo, os registros anteriores sao substituidos e a coluna installed_programs_hash e atualizada.

FR-004: Insercao em Lote de Perifericos USB
- Dispositivos USB detectados no check-in devem ser persistidos em lote em security_events atraves de uma unica chamada executemany.

FR-005: Insercao em Lote de Administradores Locais
- A sincronizacao de administradores locais deve utilizar executemany na atualizacao/insercao da tabela machine_local_admins.
```

---

## Architecture & Data Design

### 1. Schema do Banco (`backend/migrations/015_add_installed_programs_hash.sql`)
```sql
ALTER TABLE machines
ADD COLUMN IF NOT EXISTS installed_programs_hash VARCHAR(64);
```

### 2. Connection Pool (`backend/app/database.py`)
```python
from psycopg_pool import ConnectionPool

_pool: ConnectionPool | None = None
_pool_lock = threading.Lock()

def get_connection_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
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

@contextmanager
def get_connection():
    pool = get_connection_pool()
    with pool.connection() as conn:
        yield conn
```

---

## Testing Strategy

1. **Testes do Connection Pool**:
   - `backend/tests/test_database_pool.py`: verificar alocacao e retorno de conexao ao pool, limite maximo e fechamento gracioso.
2. **Testes do Throttle**:
   - `backend/tests/test_machines_throttle.py`: simular chamadas sucessivas de `mark_stale_machines_offline` garantindo que chamadas dentro de 30s nao executem query de escrita desnecessaria.
3. **Testes do Fingerprint de Programas**:
   - `backend/tests/test_installed_programs_fingerprint.py`: verificar que check-in repetido com mesmos programas mantem contagem de programas sem disparar DELETE/INSERT, e altera quando um programa e adicionado/removido.
4. **Testes de Insercao em Lote**:
   - `backend/tests/test_batch_inserts.py`: validar `create_security_events_batch` e `sync_machine_local_admins` com multiplos registros.
5. **Suite Completa de Regressao**:
   - Execucao de todos os 177+ testes existentes do backend.
