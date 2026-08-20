# Plan: EPIC 22 - Auto-atualização do Agente Windows (Updater Dedicado)

> Baseado em `spec.md` (status APPROVED, nível de rigor 4).

## Architecture

Dois lados independentes, sem tecnologia nova:

- **Backend** ganha dois endpoints de leitura (`/agent/manifest`, `/agent/download`) que servem
  um único artefato: a cópia assinada de `itcenter-agent.ps1` embutida na própria imagem Docker
  do backend (decisão da spec, seção Assumptions). Isso exige um desvio pontual de convenção
  atual: **o build context do serviço `backend` em `infra/docker-compose.production.yml` muda de
  `../backend` para a raiz do repositório**, para que `backend/Dockerfile` possa `COPY
  agent-windows/itcenter-agent.ps1` (só esse arquivo, não a pasta inteira) para dentro da imagem.
  Isso também afeta `infra/docker-compose.yml` (dev), se ele também buildar a imagem do backend
  localmente — checar antes de mexer. **Sinalizo explicitamente: este é o único desvio de
  convenção de infraestrutura desta EPIC: builds hoje têm contexto isolado por serviço; passa a
  haver uma dependência cross-diretório (backend depende de um arquivo fora de `backend/`).**
- **Agente Windows** ganha um segundo script independente (`itcenter-agent-updater.ps1`) e uma
  segunda Tarefa Agendada, reaproveitando a infraestrutura de assinatura (ADR-031) já existente.
  Nenhuma mudança estrutural em `itcenter-agent.ps1` além de: (a) declarar `$script:AgentVersion`,
  (b) incluir `agent_version` no payload, (c) manter o contador de sucesso/falha em
  `update-state.json` quando esse arquivo já existir (função nova, pequena, isolada).
- **Frontend**: mudança mínima, mesmo padrão de campo simples já usado para `mac_address`/
  `serial_number` — sem componente novo.

## Files to change

Backend:
- `backend/Dockerfile` — `COPY agent-windows/itcenter-agent.ps1 ./agent-release/itcenter-agent.ps1`
  (novo bloco `COPY`, caminho relativo à nova raiz de build context).
- `infra/docker-compose.production.yml` — `build.context: ..` + `build.dockerfile: backend/Dockerfile`
  no serviço `backend`.
- `infra/docker-compose.yml` (dev) — mesmo ajuste, se aplicável (checar se builda local ou usa
  imagem publicada).
- `backend/app/core/config.py` — nenhuma variável de ambiente nova é necessária (a versão vem do
  próprio arquivo copiado, não de env var), mas adicionar um caminho constante para o arquivo do
  release (ex.: `AGENT_RELEASE_PATH`).
- `backend/app/routes/agent.py` — adicionar `GET /manifest` e `GET /download`.
- `backend/app/schemas/agent.py` — `AgentCheckinRequest.agent_version` (novo campo opcional).
- `backend/app/schemas/machine.py` — `MachineSummary.agent_version`/`target_agent_version`.
- `backend/app/repositories/machines.py` — persistir `agent_version` em `save_machine_checkin`
  (UPSERT), incluir `agent_version`/`target_agent_version` nos `SELECT` de `list_machines`/
  `get_machine`.
- `backend/app/services/agent.py` — nenhuma mudança de lógica de detecção esperada; conferir se
  `process_agent_checkin` precisa repassar `agent_version` (repositório já cuida disso).

Agente Windows:
- `agent-windows/itcenter-agent.ps1` — `$script:AgentVersion`, incluir no payload
  (`New-AgentCheckinPayload`), nova função pequena para atualizar `update-state.json` quando
  existente (chamada ao final do ciclo, sucesso ou falha).
- `agent-windows/install-agent.ps1` — registrar a segunda Tarefa Agendada
  (`ITCenterAgentUpdater`), copiar/validar assinatura de `itcenter-agent-updater.ps1`, novo
  parâmetro `-UpdaterIntervalHours` (padrão 24) e campo `updater_interval_hours` em `config.json`.
- `agent-windows/uninstall-agent.ps1` — remover também a Tarefa Agendada `ITCenterAgentUpdater`.
- `agent-windows/scripts/Sign-AgentScripts.ps1` — adicionar `itcenter-agent-updater.ps1` à lista
  `$scriptsToSign`.

Frontend:
- `frontend/dashboard/lib/types.ts` — `agent_version`/`target_agent_version` no tipo da máquina.
- `frontend/dashboard/components/MachineDetailView.tsx` — `<DetailItem label="Versão do Agente"
  value={detail.agent_version} />`.

Documentação:
- `docs/backend/API.md` — exemplo de payload de check-in com `agent_version`; seção nova para
  `/agent/manifest` e `/agent/download`.
- `docs/backend/DATABASE.md` — colunas `agent_version`/`target_agent_version` na tabela
  `machines`.
- `docs/agent/CHECKIN.md` — campo novo no payload, lista de testes atualizada, seção sobre o
  updater (comportamento, `update-state.json`).
- `docs/agent/INSTALLATION.md` — segunda Tarefa Agendada, novo parâmetro do instalador.
- `docs/development/DECISIONS.md` (ADR-032) — nota de "Resultado" apontando para a implementação
  real e as decisões de design resolvidas nesta spec (origem do release, limites de
  rollback/confirmação), sem reabrir a decisão em si.

## Files to create

- `backend/migrations/013_machines_agent_version.sql`
- `agent-windows/itcenter-agent-updater.ps1`
- `agent-windows/tests/run-agent-updater-tests.ps1`
- `backend/tests/test_agent_manifest.py` (ou incluído em `test_agent_checkin.py` — decidir na
  implementação conforme tamanho)
- `docs/specs/epic-22-agent-auto-update/verification.md` (fase 6)

## Components

- `app/routes/agent.py` (rotas), `app/services/agent.py` (nenhuma mudança de regra SOC),
  `app/repositories/machines.py` (persistência), `app/schemas/{agent,machine}.py` (contratos).
- `agent-windows/itcenter-agent.ps1` (coleta + contador de estado), novo
  `itcenter-agent-updater.ps1` (updater), `install-agent.ps1`/`uninstall-agent.ps1` (ciclo de
  vida da 2ª Tarefa Agendada), `scripts/Sign-AgentScripts.ps1` (assinatura).
- `MachineDetailView.tsx`/`lib/types.ts` (exibição).

## Data changes

`backend/migrations/013_machines_agent_version.sql`:

```sql
ALTER TABLE machines ADD COLUMN agent_version VARCHAR(20) NULL;
ALTER TABLE machines ADD COLUMN target_agent_version VARCHAR(20) NULL;
```

Sem backfill necessário (colunas novas, `NULL` é o estado inicial correto para toda máquina
existente). Sem mudança em nenhuma outra tabela.

## API changes

- `GET /api/v1/agent/manifest` (novo) — auth `X-Agent-Api-Key`, query opcional `hostname`,
  resposta `{version, sha256, target_agent_version}` (`target_agent_version` só não-nulo se
  `hostname` bater com uma máquina cadastrada com o campo preenchido — correção feita durante a
  implementação, ver spec.md FR-001).
- `GET /api/v1/agent/download` (novo) — auth `X-Agent-Api-Key`, resposta binária
  (`application/octet-stream`).
- `POST /api/v1/agent/checkin` — payload ganha `agent_version` opcional (não é breaking change,
  campo aditivo com default `None`, mesmo padrão de `serial_number`/`mac_address` quando
  introduzidos).
- `GET /api/v1/machines`, `GET /api/v1/machines/{id}` — resposta ganha `agent_version`/
  `target_agent_version` (aditivo).

## Dependencies

Nenhuma dependência nova. Backend usa só `hashlib`/`re` (stdlib) para calcular hash e extrair
versão do arquivo; agente usa só cmdlets PowerShell nativos já usados no resto do script
(`Get-AuthenticodeSignature`, `Invoke-RestMethod`, `Move-Item`, `ConvertTo-Json`/`ConvertFrom-Json`).

## Testing Strategy

Backend (`pytest`, Postgres local via `infra/docker-compose.yml`):
- `GET /manifest` retorna `{version, sha256}` corretos para o arquivo real embutido na imagem de
  teste (ou um arquivo de fixture, se o teste não rodar dentro do container).
- `GET /manifest`/`GET /download` rejeitam requisição sem `X-Agent-Api-Key`/com chave errada
  (401), mesmo padrão de teste já usado para `/checkin`.
- `GET /download` retorna bytes cujo SHA-256 bate com o do manifest.
- Check-in com `agent_version` persiste a coluna; check-in sem o campo não quebra (compatibilidade
  retroativa, mesmo padrão dos testes de `mac_address`/`serial_number` quando opcionais).
- `GET /machines`/`GET /machines/{id}` expõem os 2 campos novos.

Agente Windows (`agent-windows/tests/run-agent-updater-tests.ps1`, dot-source, sem framework
externo — mesmo padrão de `run-agent-tests.ps1`):
- Assinatura inválida → nenhuma substituição, erro logado.
- Hash divergente → nenhuma substituição, erro logado.
- Atualização válida → `.previous` criado, script ativo trocado, `update-state.json` gravado.
- `target_agent_version` local diferente do manifest → hold-back, nenhuma substituição.
- Simulação de N falhas consecutivas de check-in → rollback restaura `.previous`.
- Simulação de N sucessos consecutivos → estado passa a "confirmado", sem rollback.
- `update-state.json` ausente → nenhum comportamento novo acionado.

`agent-windows/tests/run-agent-tests.ps1` (existente): adicionar casos para
`$script:AgentVersion` no payload e para a atualização do contador de sucesso/falha quando
`update-state.json` existir (sem quebrar os testes já existentes).

`agent-windows/tests/run-install-agent-tests.ps1` (existente): adicionar caso para registro da
2ª Tarefa Agendada e para o novo parâmetro `-UpdaterIntervalHours`.

## Migration / Rollout

- Migration `013` é aditiva/reversível (colunas `NULL`-able, sem backfill, sem risco a dados
  existentes) — mesmo padrão de baixo risco das 12 migrations anteriores.
- Mudança de build context do backend (`infra/docker-compose.production.yml`) é a única mudança
  desta EPIC com risco operacional real: exige validar que `docker compose build backend` ainda
  funciona a partir da nova raiz de contexto antes de considerar a tarefa concluída — testar
  localmente (dev compose) antes de tocar em produção; **não aplicar contra produção nesta
  sessão sem confirmação explícita**, seguindo a mesma cautela já usada nas demais mudanças de
  infra do projeto.
- Rollout do próprio agente atualizado (depois desta EPIC estar implementada) é gradual por
  natureza: cada máquina só atualiza no seu próprio ciclo do updater (~24h), sem necessidade de
  coordenação central.

## Risks

- **Mudança de build context do backend pode quebrar o pipeline de deploy existente** (scripts em
  `infra/scripts/`, CI) se algum deles assumir `context: ../backend` implicitamente. Mitigação:
  grep por `docker-compose.production.yml`/`docker compose build` em `infra/scripts/` e
  `.github/workflows/` antes de mudar, validar `docker compose config` depois.
  Local Docker builds (BuildKit) já ignoram por padrão arquivos fora do `.dockerignore`
  configurado para o context antigo — conferir se `backend/.dockerignore` precisa de ajuste para
  o novo context maior (evitar copiar `node_modules`/`.git`/etc. do repo inteiro para dentro da
  imagem).
- **Janela de rollback de até ~24h** (frequência padrão do updater) é um risco residual aceito e
  documentado na spec — mitigável por operador reduzindo `updater_interval_hours` se uma frota
  crítica exigir reação mais rápida.
- **`target_agent_version` com semântica limitada** (hold-back, não forward para versão
  arbitrária) pode gerar expectativa errada se não for bem documentado — mitigado por texto
  explícito em `docs/backend/DATABASE.md` sobre a limitação.
- **Dois processos SYSTEM periódicos por máquina** (mais superfície, já um trade-off aceito na
  ADR-032) — mitigado pela obrigatoriedade de assinatura/hash sem bypass.

## Task Breakdown

```
TASK-001 (→ FR-001, FR-002)
Criar backend/migrations/013_machines_agent_version.sql (agent_version, target_agent_version).

TASK-002 (→ Business Rules: origem do release)
Mudar infra/docker-compose.production.yml (e dev, se aplicável) para build context na raiz do
repo; ajustar backend/Dockerfile para copiar agent-windows/itcenter-agent.ps1; validar
`docker compose build backend` localmente.

TASK-003 (→ FR-001)
Implementar leitura de versão (regex $script:AgentVersion) e cálculo de sha256 do arquivo
copiado no backend (função utilitária, ex. app/services/agent_release.py ou dentro de
app/services/agent.py).

TASK-004 (→ FR-001, AC: "Manifest retorna a versão publicada")
Implementar GET /api/v1/agent/manifest em app/routes/agent.py, autenticado por
X-Agent-Api-Key, reaproveitando a mesma checagem já usada em /checkin.

TASK-005 (→ FR-002, AC: "Download serve exatamente o arquivo do manifest")
Implementar GET /api/v1/agent/download retornando os bytes do arquivo, mesma autenticação.

TASK-006 (→ FR-003, FR-004)
Adicionar agent_version opcional a AgentCheckinRequest (schemas/agent.py) e persistir em
save_machine_checkin (repositories/machines.py), incluir agent_version/target_agent_version
nos SELECT de list_machines/get_machine.

TASK-007 (→ FR-018)
Adicionar agent_version/target_agent_version a MachineSummary/MachineDetail
(schemas/machine.py).

TASK-008 (→ testes backend)
Testes: manifest/download (auth, conteúdo, hash), check-in com/sem agent_version, machines
expondo os 2 campos novos.

TASK-009 (→ FR-003)
Adicionar $script:AgentVersion ao topo de itcenter-agent.ps1 e incluir agent_version no payload
(New-AgentCheckinPayload).

TASK-010 (→ FR-013, Data Model: update-state.json)
Implementar leitura/atualização condicional de update-state.json ao final do ciclo de
itcenter-agent.ps1 (só quando o arquivo já existir).

TASK-011 (→ FR-005 a FR-012)
Criar agent-windows/itcenter-agent-updater.ps1: consulta manifest, compara versão local,
respeita target_agent_version (hold-back), valida assinatura+hash sem fallback, backup +
substituição atômica, lógica de rollback/confirmação via update-state.json.

TASK-012 (→ FR-014, FR-017)
Atualizar install-agent.ps1: copiar e validar assinatura de itcenter-agent-updater.ps1,
registrar Tarefa Agendada ITCenterAgentUpdater, novo parâmetro -UpdaterIntervalHours e campo
updater_interval_hours em config.json.

TASK-013 (→ FR-015)
Atualizar uninstall-agent.ps1 para remover também a Tarefa Agendada ITCenterAgentUpdater.

TASK-014 (→ FR-016)
Atualizar scripts/Sign-AgentScripts.ps1 incluindo itcenter-agent-updater.ps1 na lista de
scripts assinados.

TASK-015 (→ testes agente)
Criar agent-windows/tests/run-agent-updater-tests.ps1 cobrindo os cenários de aceite (assinatura
inválida, hash divergente, atualização válida, hold-back, rollback, confirmação, ausência de
estado). Atualizar run-agent-tests.ps1 (AgentVersion no payload, contador de estado) e
run-install-agent-tests.ps1 (2ª Tarefa Agendada, novo parâmetro).

TASK-016 (→ FR-019)
Adicionar agent_version a lib/types.ts e um DetailItem em MachineDetailView.tsx.

TASK-017 (→ FR-020)
Atualizar docs/backend/API.md, docs/backend/DATABASE.md, docs/agent/CHECKIN.md,
docs/agent/INSTALLATION.md e a nota de Resultado da ADR-032 em DECISIONS.md.

TASK-018
Rodar pytest completo (backend), run-agent-tests.ps1/run-install-agent-tests.ps1/
run-agent-updater-tests.ps1 (agente), npm run build (frontend). Registrar evidência em
docs/specs/epic-22-agent-auto-update/verification.md.
```
