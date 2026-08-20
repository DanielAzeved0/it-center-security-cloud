# Plan: EPIC 37 - Correção de Achados da Auditoria de Documentação (2026-08-19)

> Baseado em `spec.md` (status APPROVED). 3 trilhas independentes, implementadas em
> sequência nesta sessão (nenhuma depende da outra para funcionar).

## Architecture

Nenhum desvio de arquitetura existente nas 3 trilhas — são correções pontuais dentro de
padrões já estabelecidos (bloco Nginx espelhando um já existente; migration corrigida
in-place; detecção SOC reaproveitando a função genérica já compartilhada entre
`installed_programs` e `processes`).

## Files to change

- `infra/nginx/nginx.conf.template` — novo bloco `location` para manifest/download.
- `backend/migrations/011_installed_programs_publisher_unique.sql` — adicionar
  `DROP CONSTRAINT IF EXISTS` antes do `ADD CONSTRAINT`.
- `backend/app/services/agent.py` — mover `UNAUTHORIZED_VPN_TOOLS`/`TORRENT_TOOLS` para
  dentro de `_process_software_value()`, remover os loops inline de
  `process_installed_program_rules()`.
- `backend/tests/test_agent_checkin.py` — novos testes para VPN/Torrent via `processes`;
  confirmar que os testes existentes de dedup via `installed_programs` continuam passando
  (o `raw_data` muda de formato — ajustar asserções se algum teste existente checar o
  conteúdo exato de `raw_data` desses 2 eventos).
- `docs/deployment/KNOWN_ISSUES.md` — remover/atualizar a entrada do Nginx (corrigida).
- `docs/security/ASSET_POLICY.md` — remover a nota de "gap real" (agora corrigido).
- `docs/architecture/SECURITY.md`, `docs/security/AUTH.md`, `docs/security/SECURITY.md` —
  remover as notas de "gap conhecido (2026-08-19)" sobre o Nginx.
- `docs/development/TASKS.md` — marcar as 4 tarefas da EPIC 37 como `[x]`.

## Files to create

- Nenhum arquivo novo — as 3 trilhas são correções em arquivos já existentes.

## Components

- Nginx (`infra/nginx/`), backend SOC detection (`app/services/agent.py`), migrations
  (`backend/migrations/`).

## Data changes

Nenhuma mudança de schema. A migration 011 corrigida produz exatamente a mesma constraint
final que a versão original pretendia — só a idempotência da aplicação muda.

## API changes

Nenhuma — os 2 endpoints da Trilha 1 já existem (EPIC 22); a Trilha 1 só muda se o Nginx
deixa a chamada chegar até eles. A Trilha 3 não muda contrato de request/response do
check-in, só o comportamento interno de detecção.

## Dependencies

Nenhuma dependência nova.

## Testing Strategy

- **Trilha 1**: sem framework de teste automatizado para Nginx no repositório (confirmado na
  pesquisa) — validação manual via `curl` contra o container `nginx` local
  (`docker compose -f infra/docker-compose.yml up -d nginx`, depois `curl` para os 2 paths
  novos com e sem `X-Agent-Api-Key`, e para `/` sem `Authorization` para confirmar que o
  Basic Auth das demais rotas não foi afetado). Validação contra a VM real fica para quando
  o usuário autorizar tocar em produção (fora desta sessão, a menos que peça).
- **Trilha 2**: teste manual — aplicar a migration corrigida duas vezes seguidas contra um
  Postgres local limpo, confirmar que a segunda aplicação não falha e a constraint final é a
  esperada. Não precisa de teste automatizado novo (a automação disso é o próprio escopo da
  EPIC 33, fora desta EPIC).
- **Trilha 3**: `pytest` — 2 testes novos (VPN via `processes`, Torrent via `processes`),
  espelhando `test_agent_checkin_deduplicates_unauthorized_vpn_tool_within_same_checkin`/
  `test_agent_checkin_deduplicates_torrent_software_within_same_checkin` (EPIC 30) mas usando
  `payload.processes` em vez de `installed_programs`. Rodar a suite completa depois para
  confirmar que a mudança de `raw_data` (de `program.model_dump()` para
  `_software_detection_raw_data(...)`) não quebra nenhum teste existente que cheque o
  conteúdo de `raw_data` desses 2 eventos especificamente.

## Migration / Rollout

- Trilha 1: aplicar no Nginx local primeiro; produção só depois de validação manual
  explícita (mudança de fronteira de auth, confirmar com o usuário antes de tocar na VM real).
- Trilha 2: sem rollout — a migration ainda não foi commitada/deployada em lugar nenhum além
  de bancos de teste locais descartáveis; a correção simplesmente substitui o conteúdo do
  arquivo antes do primeiro commit real dela.
- Trilha 3: sem rollout especial — é código de detecção, ativo assim que deployado.

## Risks

- Trilha 1: um erro de sintaxe no `nginx.conf.template` derruba o Nginx inteiro (todos os
  serviços). Mitigação: `nginx -t`/`docker compose config` antes de aplicar, e validar
  localmente antes de tocar em produção.
- Trilha 3: mudar o formato de `raw_data` de `unauthorized_vpn_tool`/
  `torrent_software_detected` pode quebrar algum consumidor que dependa do formato antigo
  (`program.model_dump()`, campos `name`/`version`/`publisher`) — `_software_detection_raw_data`
  usa um formato diferente (`tool_name`/`matched_value`/`category`/`source_field`/`extra`).
  Mitigação: verificar se o dashboard ou os relatórios PDF leem `raw_data` desses 2 eventos
  especificamente antes de considerar a mudança segura (ver TASK abaixo).

## Task Breakdown

```
TASK-001 (→ FR-001, FR-002, AC: "Manifest acessível atrás do Nginx sem Basic Auth")
Adicionar bloco location para /api/v1/agent/manifest e /api/v1/agent/download em
infra/nginx/nginx.conf.template, espelhando o de /api/v1/agent/checkin, sem limit_req
(Open Question 2 confirmada).

TASK-002 (→ AC: "Dashboard e demais rotas continuam exigindo Basic Auth")
Validar localmente (docker compose up -d nginx + curl) que os 2 paths novos respondem sem
Basic Auth e que as demais rotas continuam exigindo.

TASK-003 (→ FR-003, FR-004, AC: "Migration 011 sobrevive a reaplicacao")
Adicionar DROP CONSTRAINT IF EXISTS installed_programs_machine_name_version_publisher_unique
antes do ADD CONSTRAINT em backend/migrations/011_installed_programs_publisher_unique.sql.

TASK-004 (→ AC: "Constraint final identica independente de quantas vezes a migration rodar")
Validar manualmente contra Postgres local: aplicar a migration corrigida 2x seguidas, sem
erro, constraint final correta.

TASK-005 (→ risco de raw_data)
Antes de mudar o formato de raw_data de unauthorized_vpn_tool/torrent_software_detected,
confirmar (grep no frontend/relatórios) se algum consumidor depende do formato atual
especificamente para esses 2 eventos.

TASK-006 (→ FR-005, AC: "VPN nao autorizada detectada via processo em execucao")
Mover UNAUTHORIZED_VPN_TOOLS/TORRENT_TOOLS de dentro do loop de installed_programs para
dentro de _process_software_value(), reaproveitando seen_detections já existente.

TASK-007 (→ testes)
Adicionar 2 testes novos (VPN e Torrent via processes) e rodar a suite completa para
confirmar ausência de regressão nos testes existentes de installed_programs.

TASK-008 (→ Scope: atualizar docs)
Remover as notas de "gap conhecido"/"sem correcao de codigo ainda" de
docs/deployment/KNOWN_ISSUES.md, docs/security/ASSET_POLICY.md,
docs/architecture/SECURITY.md, docs/security/AUTH.md e docs/security/SECURITY.md, refletindo
as 3 correções aplicadas. Marcar as 4 tarefas da EPIC 37 em docs/development/TASKS.md.

TASK-009
Rodar suite completa do backend (pytest) e validação manual das trilhas 1/2. Registrar em
docs/specs/epic-37-documentation-audit-fixes/verification.md.
```
