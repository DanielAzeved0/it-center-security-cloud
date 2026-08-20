# Research: EPIC 37 - Correção de Achados da Auditoria de Documentação (2026-08-19)

> Três correções pouco relacionadas entre si, agrupadas na mesma EPIC porque compartilham
> origem (auditoria de documentação de 2026-08-19) e porte pequeno. Tratadas como 3 trilhas
> independentes na spec.

## Arquitetura existente relevante

**Trilha 1 (Nginx):** `infra/nginx/nginx.conf.template` já tem o padrão exato a seguir —
`location = /api/v1/agent/checkin` (linhas 65-78) é isento de `auth_basic` (por omissão da
diretiva, não por override explícito), com `proxy_pass http://backend:8000`, headers
(`Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`, `X-Agent-Api-Key`) e timeouts
próprios. `limit_req zone=agent_checkins burst=20 nodelay` é específico do volume de
check-in (a cada poucos minutos por máquina) — não necessariamente aplicável a
manifest/download (consultados pelo updater 1x/dia por máquina, volume bem menor).

**Trilha 2 (migration 011):** `backend/apply_migrations.py` reaplica todos os `.sql` de
`backend/migrations/` em todo start do container (sem tabela de controle — gap já rastreado
como teste pendente na EPIC 33). Migrations `009`/`010`/`012` usam `ADD COLUMN IF NOT
EXISTS`/`CREATE UNIQUE INDEX IF NOT EXISTS`/`DROP CONSTRAINT IF EXISTS` corretamente.
`011_installed_programs_publisher_unique.sql` faz `DROP CONSTRAINT IF EXISTS` (da constraint
antiga) seguido de `ADD CONSTRAINT ... UNIQUE (...)` **sem guarda** — Postgres não tem `ADD
CONSTRAINT IF NOT EXISTS`, então a segunda aplicação falha. **Esta migration ainda não foi
commitada nem deployada** (confirmado: `git status` mostra `backend/migrations/011_*.sql`
como untracked) — não é uma migration "em produção" que precise de forward-fix via nova
migration, pode ser corrigida in-place no próprio arquivo `011`.

**Trilha 3 (VPN/Torrent via processes):** `backend/app/services/agent.py`,
`process_installed_program_rules()` (linha 274). Há uma função compartilhada,
`_process_software_value()` (linha 174), chamada tanto para `installed_programs` quanto para
`processes`, que já lida genericamente com 4 categorias (`AUTHORIZED_REMOTE_TOOLS`,
`UNAUTHORIZED_REMOTE_TOOLS`, `MALWARE_OR_RANSOMWARE_INDICATORS`, `DUAL_USE_TOOLS`) via
`source_field`/`extra` (permitindo `extra=None` quando chamada para `processes`, que não tem
metadados de versão/publisher). `UNAUTHORIZED_VPN_TOOLS`/`TORRENT_TOOLS`, ao contrário,
**não** passam por `_process_software_value()` — estão inline dentro do loop `for program in
payload.installed_programs`, usando `program.model_dump()` diretamente como `raw_data`
(porque só existe o objeto `program` ali, não em `processes`). É por isso que a cobertura
não se estende a `processes` hoje — não foi uma decisão consciente registrada em nenhum ADR,
é a mesma lacuna que a auditoria de documentação encontrou.

## Funcionalidade semelhante já implementada

- O padrão de deduplicação `seen_detections: set[tuple[str, str]]` já existe e já é
  compartilhado entre as 6 categorias de detecção (as 4 genéricas + VPN + Torrent) — extender
  VPN/Torrent para `processes` reaproveita a mesma infraestrutura, não cria nada novo.
- `_software_detection_raw_data()` (helper já existente, não lido aqui em detalhe mas usado
  pelas 4 categorias genéricas) é o formato de `raw_data` a seguir se VPN/Torrent for movido
  para dentro de `_process_software_value()`, em vez de continuar usando
  `program.model_dump()` (que só existe no contexto de `installed_programs`).

## Convenções a seguir

- Migrations: `BEGIN;`/`COMMIT;`, sempre com guarda de idempotência
  (`IF EXISTS`/`IF NOT EXISTS`), nunca destrutivas sem necessidade.
- Nginx: comentário explicando a razão da isenção de Basic Auth antes de cada `location`
  (já é o padrão nos 2 blocos existentes, `/agent/checkin` e `/api/backend/`).
- Validação de mudança de Nginx: manual, via `curl` contra o ambiente real — não existe
  nenhum teste automatizado de `nginx.conf.template` no repositório hoje (confirmado por
  busca); a EPIC 28-B já validou uma correção de Nginx dessa forma ("Confirmado ao vivo (build
  + request real)"), sem framework de teste dedicado.
- Detecção SOC: toda regra nova/alterada precisa atualizar `docs/security/ASSET_POLICY.md` e
  `docs/security/SOC_RULES.md` antes ou junto da implementação (regra dura do `CLAUDE.md`).

## Decisões arquiteturais relevantes

- Nenhuma ADR cobre especificamente nenhuma das 3 trilhas — são bugs/gaps, não decisões de
  arquitetura. Não deve ser necessária uma ADR nova para nenhuma das 3 (mudança pontual,
  reversível, sem novo componente/tecnologia).
- ADR-036 (segredo por máquina) e ADR-032 (updater) são o contexto que tornou a Trilha 1
  visível — o gap sempre existiu na superfície do Nginx, mas só importa agora que existe um
  cliente (`itcenter-agent-updater.ps1`) que depende de `/manifest`/`/download` funcionarem
  atrás do Nginx.

## Testes existentes relacionados

- Trilha 1: nenhum teste automatizado de Nginx. Validação será manual (`curl`).
- Trilha 2: nenhum teste hoje aplica a mesma migration duas vezes seguidas contra o mesmo
  banco (gap rastreado na EPIC 33, não desta EPIC) — a correção da Trilha 2 pode ser validada
  manualmente (aplicar `011` duas vezes contra um Postgres local) sem esperar a EPIC 33.
- Trilha 3: `backend/tests/test_agent_checkin.py` já tem os testes de
  `test_agent_checkin_deduplicates_unauthorized_vpn_tool_within_same_checkin` e
  `test_agent_checkin_deduplicates_torrent_software_within_same_checkin` (EPIC 30) — cobrem
  dedup dentro de `installed_programs`, não cobrem `processes`. Um teste novo replicando o
  padrão desses dois, mas usando `payload.processes`, é o caminho natural.

## Dependências e integrações

- Trilha 1 depende só de editar `infra/nginx/nginx.conf.template` — sem dependência de
  código Python/PowerShell. Precisa de rebuild/restart do container `nginx` para valer
  (`docker compose ... up -d nginx` ou equivalente, sem afetar os demais serviços).
- Trilha 2 é isolada em um único arquivo de migration, sem dependência de outras trilhas.
- Trilha 3 depende só de `backend/app/services/agent.py` + os 2 docs de segurança.

## Regras do repositório

- `CLAUDE.md`: mudança de regra de detecção exige atualizar `ASSET_POLICY.md`/`SOC_RULES.md`
  antes/junto (relevante para a Trilha 3, se a decisão for estender).
- Nenhuma das 3 trilhas introduz tecnologia nova, tabela nova ou endpoint novo — não há
  necessidade de ADR pelas regras do projeto.

## Perguntas em aberto levadas para Requirements Discovery

1. **Trilha 3 é a única com uma decisão real de escopo, não uma correção óbvia**: estender
   `UNAUTHORIZED_VPN_TOOLS`/`TORRENT_TOOLS` para também avaliar `payload.processes` (fechando
   a lacuna real de detecção) ou manter a limitação atual e já documentada (só
   `installed_programs`), aceitando-a conscientemente? A EPIC 37 registrou isso como "decidir
   e implementar" — decisão pertence ao usuário, não vai ser assumida em silêncio.
2. Trilha 1: `limit_req` do check-in não deve necessariamente se aplicar a
   manifest/download (volume bem menor, 1x/dia por máquina) — confirmar que não aplicar
   rate-limit a esses 2 endpoints é aceitável, ou se algum limite (mais frouxo) é desejado.
