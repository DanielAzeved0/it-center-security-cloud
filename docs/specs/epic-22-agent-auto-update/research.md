# Research: EPIC 22 - Auto-atualização do Agente Windows (Updater Dedicado)

> Investigação feita antes de especificar. Baseada em ADR-032 (`docs/development/DECISIONS.md`),
> `docs/development/TASKS.md` (EPIC 22) e leitura direta do código atual.

## Arquitetura existente relevante

**Agente Windows (`agent-windows/`):**

- `itcenter-agent.ps1`: script único de coleta, executado pela Tarefa Agendada `ITCenterAgent`
  (registrada por `install-agent.ps1`) a cada `checkin_interval_minutes` (padrão 5 min), rodando
  como `SYSTEM`. Sem versão declarada hoje (`$script:AgentVersion` ainda não existe).
- `install-agent.ps1`: valida input, testa conectividade (DNS/TCP/health), importa o certificado
  de assinatura (`itcenter-agent-signing.cer`) no `LocalMachine\Root`/`TrustedPublisher` via
  `certutil.exe` (não a API `.NET X509Store`, que pode travar num prompt de segurança), valida
  assinatura Authenticode dos 3 scripts (`Assert-AgentScriptSignature`), grava `config.json`,
  restringe ACL de `config.json`/`logs\`/`cache\` a `SYSTEM`/`Administrators` (`Protect-AgentPath`,
  com `ContainerInherit, ObjectInherit` para diretórios) e registra a Tarefa Agendada com
  `ExecutionPolicy AllSigned` (ou `Bypass` só com `-SkipSignatureCheck`, fallback local/dev).
- `uninstall-agent.ps1`: remove a Tarefa Agendada `ITCenterAgent`, opcionalmente remove arquivos,
  certificado (`certutil -delstore`, buscando pelo `Subject` do certificado) e dados
  (`logs\`/`cache\`).
- `scripts/New-AgentSigningCertificate.ps1` / `scripts/Sign-AgentScripts.ps1`: geração do
  certificado self-signed (ADR-031) e assinatura. `Sign-AgentScripts.ps1` tem uma lista
  **hardcoded** de 3 scripts (`itcenter-agent.ps1`, `install-agent.ps1`, `uninstall-agent.ps1`) —
  qualquer script novo (o updater) precisa ser adicionado a essa lista manualmente.
- `agent-windows/tests/run-agent-tests.ps1`: dot-source do script + funções `Assert-*` próprias
  (sem framework de teste externo, consistente com "sem dependências").

**Backend:**

- `app/routes/agent.py`: hoje só tem `POST /api/v1/agent/checkin`, autenticado comparando
  `X-Agent-Api-Key` (header) contra `settings.agent_api_key` (`AGENT_API_KEY` de ambiente) via
  `hmac.compare_digest`. Nenhum RBAC de usuário humano aqui — é autenticação de classe (agente),
  não de indivíduo.
- `app/schemas/agent.py` / `app/services/agent.py` / `app/repositories/machines.py`:
  `process_agent_checkin` chama `save_machine_checkin` (UPSERT em `machines` por `hostname`,
  dentro de uma transação com `SELECT ... FOR UPDATE`), captura `MachineIdentityMismatch` e grava
  um `security_event`/alerta `machine_identity_mismatch` antes de devolver 401 (ADR-036).
- `app/schemas/machine.py` + `app/routes/machines.py`: padrão já estabelecido para campos novos
  em `machines` — schema (`MachineSummary`/`MachineDetail`) expõe o campo, `list_registered_machines`/
  `get_registered_machine` fazem `SELECT` explícito (sem `SELECT *`), RBAC via
  `Depends(require_roles(...))`. Endpoint de escrita administrativa (`PATCH /machines/{id}/rustdesk`)
  segue o padrão: `require_roles("admin", "analyst")` + `create_audit_log(...)` com
  `action="machine.rustdesk_update"`.
- `backend/migrations/`: 12 migrations aplicadas (`001`...`012`), sempre aditivas/forward-only,
  coluna nova sempre `NULL`-able quando o dado pode faltar. Próxima seria `013_*.sql`.
- `backend/Dockerfile`: `COPY app ./app`, `COPY migrations ./migrations`,
  `COPY apply_migrations.py .` — **`agent-windows/` não é copiado para a imagem do backend**, e
  `infra/docker-compose.production.yml` não monta nenhum volume de `agent-windows/` no container
  `backend` (`build: context: ../backend`, sem volume extra). Ou seja, hoje **não existe nenhum
  mecanismo pelo qual o backend em produção enxergue o conteúdo de `agent-windows/`** — isso é uma
  lacuna real de design que a ADR-032 não resolveu (ela diz que o backend "passa a servir" o
  manifest/download, mas não diz de onde o backend lê os bytes/versão/hash).

**Frontend:**

- `lib/types.ts` espelha os campos do `MachineSummary`/`MachineDetail` do backend.
- `MachineDetailView.tsx` exibe cada campo simples via `<DetailItem label="..." value={detail.campo} />`
  (ex.: linha 290-291 para `mac_address`/`serial_number`) — padrão direto para `agent_version`.

## Funcionalidade semelhante já implementada

- **Ciclo HTTP com retry/classificação de falha** já existe em `itcenter-agent.ps1` (temporária vs.
  permanente, atraso progressivo) — o updater pode reaproveitar a mesma lógica de requisição, mas
  é um script separado (ADR-032 exige updater dedicado, não acoplado ao processo de coleta).
- **Infra de assinatura de código (ADR-031)** já resolve o requisito "validação obrigatória de
  assinatura Authenticode" do updater — `Get-AuthenticodeSignature`/`Assert-AgentScriptSignature`
  já existem como função em `install-agent.ps1` e podem ser extraídas/reaproveitadas.
- **Coluna opcional + endpoint de escrita administrativa** já tem um exemplo direto:
  `rustdesk_id` (nullable, migration dedicada) + `PATCH /machines/{id}/rustdesk` (RBAC
  admin/analyst + audit log). Isso é o modelo mais próximo para pensar em como
  `target_agent_version` seria escrito por um operador — **mas o backlog da EPIC 22
  (`docs/development/TASKS.md`) não lista nenhum endpoint PATCH nem UI de dashboard para
  `target_agent_version`**, só a coluna e o updater lendo-a. Ver Open Question abaixo.
- **Trust-on-first-use / segredo por máquina (ADR-036)** é uma integração recente e é o único
  precedente de "novo dado de segurança sensível trafegando no check-in" — relevante como
  referência de rigor, mas não diretamente reaproveitável aqui (o updater não é o check-in).

## Convenções a seguir

- PowerShell: funções `Get-Agent*`/`ConvertTo-Agent*`/`Assert-Agent*`, `$ErrorActionPreference = "Stop"`
  no topo, try/catch explícito por função que não deve derrubar o fluxo principal (ver EPIC 16/31),
  throw com mensagem acionável nas funções de validação.
- Backend: rotas finas (`app/routes/*.py`) delegando para `app/services/*.py`
  (regra de negócio) e `app/repositories/*.py` (SQL puro via `psycopg`, sem ORM); schemas Pydantic
  separados por domínio (`app/schemas/agent.py`, `app/schemas/machine.py`).
- Migrations: um arquivo por mudança, nome `NNN_descricao.sql`, sempre aditivo.
- Documentação: `docs/backend/API.md` (contrato com exemplo JSON), `docs/backend/DATABASE.md`
  (schema + seção "Regras"), `docs/agent/CHECKIN.md` (comportamento do agente + lista de testes),
  `docs/agent/INSTALLATION.md` (fluxo de instalação) — todos atualizados **no momento da
  implementação**, não antes (mesmo padrão das EPICs 19/20/21/27).
- Testes: `backend/tests/test_*.py` (pytest, Postgres local via `infra/docker-compose.yml`);
  `agent-windows/tests/run-*-tests.ps1` (dot-source + asserts próprios, sem framework externo).

## Decisões arquiteturais relevantes

- **ADR-032** (a decisão que esta EPIC implementa): updater dedicado 100% PowerShell puro, Tarefa
  Agendada própria (`ITCenterAgentUpdater`) com frequência menor que o check-in (sugestão 1x/dia,
  configurável), backend serve `GET /api/v1/agent/manifest` (`{version, sha256}`) e
  `GET /api/v1/agent/download`, ambos autenticados por `X-Agent-Api-Key` (mesmo mecanismo do
  check-in — **não** o `agent_secret` por máquina do ADR-036, que é específico do check-in).
  Validação obrigatória de assinatura + hash, **sem fallback de bypass** (diferente do instalador).
  Backup atômico (`itcenter-agent.ps1.previous` + `Move-Item -Force`). Auto-rollback após N
  check-ins consecutivos com falha (N não definido na ADR — "a definir na implementação").
  `machines.target_agent_version` permite rollout controlado por máquina. Identidade individual
  por agente (API key por máquina) e revogação continuam **fora de escopo**.
- **ADR-031**: infraestrutura de certificado/assinatura já existe e deve ser reaproveitada, não
  recriada. Importante: o updater **nunca** pode ter um fallback equivalente ao
  `-SkipSignatureCheck` do instalador — a ADR-032 é explícita sobre isso ("diferente do instalador
  ... o updater nunca aceita esse fallback, por operar contra rede/backend").
- **ADR-025 / ADR-005**: agente 100% PowerShell puro, sem dependências externas novas — o updater
  não pode introduzir nenhuma lib/módulo de terceiro.
- **ADR-036**: `AGENT_API_KEY` global continua sendo a autenticação de classe do agente; segredo
  por máquina é específico do check-in (`/agent/checkin`), não necessariamente estendido aos
  endpoints novos — a ADR-032 já decidiu que manifest/download usam só `X-Agent-Api-Key`.

## Testes existentes relacionados

- Nenhum teste cobre atualização/updater hoje (funcionalidade inexistente).
- `agent-windows/tests/run-agent-tests.ps1` e `run-install-agent-tests.ps1` são os dois harnesses
  existentes de agente Windows — um terceiro (`run-agent-updater-tests.ps1`, nome hipotético) seria
  o padrão natural para o novo script, seguindo a mesma convenção de nome/estrutura.
- `backend/tests/test_agent_checkin.py` e `backend/tests/test_machines.py` (RBAC/listagem) são os
  equivalentes de backend a seguir para os 2 endpoints novos e as 2 colunas novas.

## Dependências e integrações

- **Certificado de assinatura (ADR-031)**: o updater depende de o script baixado já estar assinado
  *antes* de chegar ao backend — a assinatura acontece em `Sign-AgentScripts.ps1` (processo manual
  do mantenedor), não em tempo de request.
- **Armazenamento do "release" do agente no backend**: gap real identificado acima — precisa de
  decisão explícita (ver Open Questions) sobre onde o backend lê o script/versão/hash a servir.
- **Tarefa Agendada dupla por máquina**: mais um processo periódico com privilégio `SYSTEM`
  (ADR-032 já assume esse trade-off, mitigado pela validação de assinatura obrigatória).

## Regras do repositório

- `CLAUDE.md`: Kubernetes/RabbitMQ/Kafka/Redis/microsserviços/Elasticsearch proibidos — não se
  aplica aqui (nenhuma dessas tecnologias é candidata). Qualquer tabela/endpoint novo deve ser
  documentado em `docs/architecture/`/`docs/backend/DATABASE.md`/`docs/backend/API.md` antes ou
  junto da implementação — já é o padrão que a EPIC 22 pretende seguir (ADR-032 já registra isso).
  Mudança que toca autenticação/dados de máquina deve considerar OWASP Top 10 — relevante aqui
  porque isto é, na prática, um mecanismo de atualização remota de código rodando como `SYSTEM`
  disparado por uma resposta HTTP do backend: um manifest/download comprometido (backend
  invadido, ou o mecanismo de origem do arquivo do Open Question abaixo mal desenhado) vira
  execução de código arbitrário em toda a frota. Isso justifica tratar esta spec com o nível de
  rigor mais alto do skill (Level 4) e uma seção explícita de Security Requirements/ameaças.

## Perguntas em aberto levadas para Requirements Discovery

1. **De onde o backend lê o script/versão/hash "mais recente" a servir?** Nem a ADR-032 nem o
   backlog da EPIC 22 resolvem isso, e a investigação de código confirma que hoje não há nenhum
   mecanismo (`agent-windows/` não entra na imagem Docker do backend nem é montado por volume).
   Pelo menos 3 caminhos plausíveis, com trade-offs bem diferentes de runbook de deploy:
   - (A) `COPY` do script assinado para a imagem do backend no build (`backend/Dockerfile`) +
     versão/hash gerados em build-time ou via variável de ambiente — republicar agente = rebuild/
     redeploy do backend, sem infraestrutura nova.
   - (B) Volume montado no container `backend` apontando para um diretório de "releases" na VM
     (ex.: `/opt/itcenter/agent-releases`), atualizado manualmente pelo mantenedor — desacopla o
     ciclo de release do agente do redeploy do backend, mas é um runbook novo, não documentado
     hoje.
   - (C) Guardar os bytes do script (e metadados) numa tabela nova no Postgres — descarta a
     necessidade de tocar no Dockerfile/volumes, mas é um uso atípico do banco (achado binário
     versionado) para um projeto que hoje só usa Postgres para dados operacionais.
2. **Como o operador define `machines.target_agent_version`?** A ADR-032 registra a coluna e sua
   finalidade (rollout/canário), mas nem a ADR nem o backlog da EPIC 22 listam um endpoint PATCH
   ou UI de dashboard para escrevê-la — só o updater lendo-a é mencionado. Confirmar se o escopo
   real desta EPIC é "coluna existe, escrita é só via SQL manual do operador" (consistente com o
   backlog atual) ou se falta um endpoint administrativo equivalente ao `PATCH .../rustdesk`.
3. **Qual o mecanismo concreto de "N check-ins consecutivos com falha pós-atualização"?** A
   ADR-032 deixa N "a definir na implementação", mas não deixa claro *como* o updater (processo/
   Tarefa Agendada separada) saberia quantos check-ins de coleta falharam desde a última
   atualização — o script de coleta hoje não persiste um contador de falhas consecutivas entre
   execuções. Precisa de um mecanismo de estado compartilhado (ex.: um arquivo JSON pequeno que o
   coletor atualiza a cada execução e o updater lê) — proposto na spec, mas o valor de N e o
   mecanismo exato ficam como decisão explícita a confirmar.
4. **Frequência padrão da Tarefa Agendada do updater**: ADR-032 sugere "1x/dia, configurável" —
   confirmar se este é o padrão aceito para a spec.
