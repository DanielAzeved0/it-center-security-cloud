# Verification: EPIC 37 - Correção de Achados da Auditoria de Documentação (2026-08-19)

## Acceptance criteria

```
[x] Scenario: Manifest acessível atrás do Nginx sem Basic Auth — passou (curl real contra Nginx oficial + backend real: 401 do FastAPI, sem www-authenticate)
[x] Scenario: Download acessível atrás do Nginx sem Basic Auth — passou (mesmo padrão)
[x] Scenario: Dashboard e demais rotas continuam exigindo Basic Auth — passou (401 com www-authenticate: Basic, inalterado)
[x] Scenario: Migration 011 sobrevive a reaplicacao — passou (aplicada 2x seguidas contra Postgres local, sem erro)
[x] Scenario: Constraint final identica independente de quantas vezes a migration rodar — passou (UNIQUE (machine_id, name, version, publisher) confirmada via \d installed_programs)
[x] Scenario: VPN nao autorizada detectada via processo em execucao — passou (test_agent_checkin_detects_unauthorized_vpn_tool_via_processes)
[ ] Scenario: Nenhuma mudanca de comportamento (limitacao mantida) — não aplicável, decisão foi estender (FR-005), não manter (FR-006)
```

## Tests

Backend (`python -m pytest -q`, Postgres local via `infra/docker-compose.yml`, `DATABASE_URL` em `127.0.0.1`): **125 passed** (123 anteriores + 2 novos de Trilha 3).

Nginx (Trilha 1): sem framework automatizado no repositório (confirmado na pesquisa) — validação manual real:
- `nginx:1.28-alpine` oficial + `infra-backend`/`infra-frontend` reais (dev, rebuild após o fix da migration 011) na mesma rede Docker (`infra_default`), com certificado dummy self-signed para TLS.
- `GET /agent/manifest` sem `X-Agent-Api-Key` → `401` (corpo JSON do FastAPI, sem header `www-authenticate`).
- `GET /agent/manifest` com `X-Agent-Api-Key: change-me` → `200` com o manifest real (`{"version":"1.0.0","sha256":"...","target_agent_version":null}`).
- `GET /agent/download` sem `X-Agent-Api-Key` → `401` (mesmo padrão).
- `GET /` (dashboard) sem `Authorization` → `401` com `www-authenticate: Basic realm="IT Center Security Cloud"` (Nginx, inalterado).
- `POST /agent/checkin` com corpo vazio → `422` (chega ao FastAPI normalmente, sem regressão).

Migration 011 (Trilha 2): aplicada manualmente 2x seguidas contra Postgres local via `docker exec -i itcenter-postgres psql ... < 011_installed_programs_publisher_unique.sql` — segunda aplicação não gerou erro (`NOTICE: constraint ... does not exist, skipping` para a constraint antiga, `ALTER TABLE` bem-sucedido para o resto). Reprodução adicional do bug original: o container `backend` dev, ao subir com uma imagem construída *antes* da correção (mas com a constraint nova já presente no banco, por causa do teste manual anterior), entrou no exato crash-loop `DuplicateTable` previsto — rebuild com o arquivo corrigido resolveu e o container ficou `healthy`.

## Regression check

Suite completa do backend (125 testes) sem nenhuma regressão, incluindo os testes existentes de dedup de VPN/Torrent via `installed_programs` (que continuam passando apesar da mudança de formato interno de `raw_data`, confirmando que nenhum teste dependia do formato antigo). `docker compose build backend` e `up -d backend frontend` bem-sucedidos com a migration corrigida.

## Spec drift encontrado

Nenhum. As 2 Open Questions da spec foram respondidas pelo usuário antes da implementação (estender Trilha 3; sem rate limit próprio na Trilha 1) e a implementação seguiu exatamente o decidido — sem descoberta que exigisse revisar a spec depois de aprovada.

## Segurança

- Trilha 1 é uma mudança de fronteira de autenticação em produção — validada com cuidado extra (blocos `location =` exatos, não regex, para não capturar mais do que o pretendido; contraste explícito de headers entre o 401 do Nginx e o 401 do FastAPI para confirmar que a mudança tem o efeito exato pretendido, nem mais nem menos).
- Trilha 3 amplia detecção (mais visibilidade de SOC), não reduz nenhuma proteção existente.
- Nenhuma das 3 trilhas expõe dado novo, remove autenticação ou muda RBAC.

## Escopo

Nenhuma mudança fora do combinado no plano. As 3 trilhas ficaram isoladas nos arquivos previstos (`infra/nginx/nginx.conf.template`, `backend/migrations/011_*.sql`, `backend/app/services/agent.py` + teste correspondente), mais a atualização de documentação combinada (5 docs de segurança/arquitetura + `KNOWN_ISSUES.md` + `ROADMAP.md` + `docs/agent/README.md`/`TROUBLESHOOTING.md`).

## Sign-off

Status final: **VERIFIED** para as Trilhas 2 e 3 (código corrigido, testado, documentado, sem pendência). Trilha 1 está **VERIFIED em ambiente local**, mas **não deployada em produção** — `itcenter-edge-01` continua rodando o `nginx.conf.template` anterior até o próximo deploy real incluir este commit; todos os docs tocados nesta EPIC foram redigidos para deixar essa distinção explícita, evitando reproduzir o mesmo tipo de lacuna (código pronto vs. código rodando de fato) que originou esta própria EPIC.
