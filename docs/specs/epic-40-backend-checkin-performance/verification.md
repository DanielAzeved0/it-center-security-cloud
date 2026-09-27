# Verification Report: EPIC 40 - Desempenho do Backend no Check-in

## 1. Contexto e Objetivos

A EPIC 40 otimizou o desempenho do fluxo de check-in do agente e das consultas do dashboard no FastAPI, abordando os 4 principais gargalos identificados na auditoria de qualidade:
1. Overhead de abertura repetida de conexões TCP ao PostgreSQL por requisição (resolvido com `psycopg_pool.ConnectionPool`).
2. Varreduras globais de escrita em `mark_stale_machines_offline` atreladas a leituras de dashboard (resolvido com throttle de 30s).
3. Ciclos desnecessários de `DELETE` + centenas de `INSERT` em `installed_programs` (resolvido com hashing SHA-256 e coluna `installed_programs_hash`).
4. Inserções sequenciais linha a linha de eventos USB e administradores locais (resolvido com `cursor.executemany` e transações atômicas).

---

## 2. Testes Automatizados e Evidências

### 2.1 Testes Unitários e de Integração Desenvolvidos

- `backend/tests/test_database_pool.py`:
  - `test_connection_pool_reuses_connections`: Valida reutilização de conexões e integridade do pool (min_size=1, max_size=5).
  - `test_lifespan_closes_connection_pool`: Valida que o encerramento da aplicação via lifespan fecha o connection pool graciosamente.
- `backend/tests/test_machines_stale_throttle.py`:
  - `test_mark_stale_machines_offline_throttled`: Valida que varreduras globais (`machine_id=None`) dentro da janela de 30s são suprimidas.
  - `test_mark_stale_machines_offline_specific_machine_bypasses_throttle`: Valida que chamadas com `machine_id` específico executam imediatamente sem debounce.
- `backend/tests/test_installed_programs_fingerprint.py`:
  - Valida hashing determinístico SHA-256, ordenação estável e normalização de strings.
  - `test_save_machine_checkin_skips_unchanged_installed_programs`: Valida que registros e IDs originais em `installed_programs` são preservados sem re-inserção.
  - `test_save_machine_checkin_updates_changed_installed_programs`: Valida que modificações na lista de programas disparam atualização do hash e recriação dos itens.
  - `test_update_machine_installed_programs_with_connection`: Valida assinatura tipada e execução com conexão externa.
- `backend/tests/test_security_events_batch.py`:
  - Valida inserção em lote de eventos USB com `cursor.executemany`, tratamento seguro de lista vazia e execução sob conexão externa opcional.
- `backend/tests/test_local_admins_batch.py`:
  - Valida batching via `cursor.executemany` com UPSERT e preservação de histórico `last_seen_at` e detecção de delta de novos administradores locais.

### 2.2 Execução da Suíte Completa

```bash
.venv\Scripts\python.exe -m pytest backend/tests/ -v
```

**Resultado:**
- **196 passed**, 1 warning em ~17.5s.
- 0 falhas, 0 quebras de contrato ou regressões em autenticação, risk engine, check-in, relatórios ou máquinas.

---

## 3. Verificação de Restrições Globais

| Restrição | Status | Evidência |
|---|---|---|
| Stack pura psycopg + psycopg_pool (zero ORM/SQLAlchemy) | Aprovado | `requirements.txt` com `psycopg-pool>=3.2.0`, sem dependências externas adicionais. |
| Assinatura `get_connection()` 100% retrocompatível | Aprovado | Context manager preservado em todos os repositórios existentes (`with get_connection() as conn:`). |
| Pool dimensionado para VM de 954MB | Aprovado | `min_size=1`, `max_size=5`, `timeout=10.0`, `max_idle=300.0`. |
| Migration 015 idempotente | Aprovado | `ALTER TABLE machines ADD COLUMN IF NOT EXISTS installed_programs_hash VARCHAR(64);`. |
| Zero degradação funcional nos alertas de segurança | Aprovado | Detecção de novos administradores (`new_admin_user`) e eventos USB preservada com paridade total. |

---

## 4. Status Final

EPIC 40 concluída com êxito, auditada por subagentes e pronta para publicação e deploy contínuo em produção.
