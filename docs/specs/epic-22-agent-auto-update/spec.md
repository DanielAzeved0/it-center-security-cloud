# Spec: EPIC 22 - Auto-atualização do Agente Windows (Updater Dedicado)

## Metadata

- Status: VERIFIED (ver verification.md)
- Nível de rigor: 4 (crítico) — mecanismo de atualização remota de código rodando como `SYSTEM`
  em toda a frota monitorada, disparado por uma resposta HTTP do backend. Um manifest/download
  comprometido (ou mal desenhado) vira execução de código arbitrário em massa — trata-se, na
  prática, de um problema de supply chain interno.
- Autor/origem: ADR-032 (`docs/development/DECISIONS.md`) + EPIC 22 (`docs/development/TASKS.md`)
  + `/sdd` (sessão 2026-08-19), aprovado pelo usuário nesta mesma sessão.
- Data: 2026-08-19
- Dependências: ADR-031 (infra de assinatura de código), ADR-025/ADR-005 (agente PowerShell puro),
  ADR-036 (autenticação do agente — não é estendida aqui).

## Context

O agente Windows não tem hoje nenhum mecanismo de atualização: toda correção ou evolução exige
reinstalar manualmente `install-agent.ps1` em cada máquina, o que não escala com o crescimento da
frota monitorada. A ADR-032 já decidiu a arquitetura (updater dedicado, 100% PowerShell, Tarefa
Agendada própria, validação obrigatória de assinatura+hash, backup/rollback automático) — esta
spec transforma essa decisão em requisitos verificáveis e resolve as lacunas de design que a ADR
deixou explicitamente em aberto ("a definir na implementação").

## Goal

Uma máquina monitorada recebe atualizações do agente de coleta automaticamente, sem intervenção
manual, com validação de assinatura/hash obrigatória e recuperação automática se a atualização
quebrar o check-in.

## Scope

- Dois endpoints novos no backend: `GET /api/v1/agent/manifest` e `GET /api/v1/agent/download`,
  autenticados por `X-Agent-Api-Key` (mesmo mecanismo do check-in).
- Duas colunas novas em `machines`: `agent_version`, `target_agent_version`.
- `itcenter-agent.ps1` passa a declarar `$script:AgentVersion` e a enviar `agent_version` no
  payload de check-in.
- Novo script `agent-windows/itcenter-agent-updater.ps1`: baixa, valida (assinatura + hash),
  faz backup atômico, substitui, e implementa auto-rollback por falha pós-atualização.
- Nova Tarefa Agendada `ITCenterAgentUpdater`, registrada por `install-agent.ps1`.
- `agent_version` exibido no dashboard (`MachineDetailView.tsx`).
- Mecanismo de origem do "release" do agente no backend (lacuna que a ADR-032 não resolveu —
  ver Business Rules e Assumptions).
- Atualização de `docs/backend/API.md`, `docs/backend/DATABASE.md`, `docs/agent/CHECKIN.md`,
  `docs/agent/INSTALLATION.md`.

## Out of Scope

- Identidade individual por agente (API key por máquina) e revogação de agentes comprometidos —
  explicitamente fora do escopo da ADR-032, permanece pendente na Fase B.
- Endpoint/UI administrativo para **escrever** `machines.target_agent_version` — o backlog da
  EPIC 22 não lista essa peça; a coluna existe e é lida pelo updater, mas o valor é escrito
  manualmente via SQL pelo operador nesta rodada (ver Assumptions).
- Histórico de múltiplas versões do agente servidas simultaneamente pelo backend (release
  versionado de verdade) — o backend serve sempre "a versão atualmente publicada" (a que está
  na imagem Docker corrente), não uma versão arbitrária do passado. Ver Business Rules sobre o
  que isso implica para `target_agent_version`.
- Serviço Windows nativo via SCM para a coleta em si (caso genérico da Fase B) — inalterado.
- Compressão/assinatura de payload de check-in, empacotamento independente do agente — inalterado.

## Functional Requirements

```
FR-001
O backend deve expor GET /api/v1/agent/manifest, autenticado por X-Agent-Api-Key, retornando
{version, sha256} da versão do agente atualmente publicada pelo backend. O endpoint aceita um
parâmetro de query opcional hostname; quando informado e houver uma máquina cadastrada com esse
hostname e target_agent_version preenchido, a resposta inclui também target_agent_version (null
caso contrário). Correção feita durante a implementação: a primeira versão desta spec dizia que
o updater deveria respeitar machines.target_agent_version (FR-007) sem dar a ele nenhuma forma de
descobrir esse valor - o updater só tem X-Agent-Api-Key (sem RBAC/identidade individual), então
o manifest precisa aceitar o hostname (mesmo sinal de identidade já usado no check-in) para
devolver o valor certo. Isso não piora a superfície de exposição: um hostname já é informação
que qualquer titular da AGENT_API_KEY compartilhada já vê no restante do fluxo.

FR-002
O backend deve expor GET /api/v1/agent/download, autenticado por X-Agent-Api-Key, retornando os
bytes exatos do script itcenter-agent.ps1 cujo sha256 é o mesmo devolvido por /manifest.

FR-003
itcenter-agent.ps1 deve declarar $script:AgentVersion no topo do script e incluir agent_version
no payload de POST /api/v1/agent/checkin.

FR-004
O backend deve persistir agent_version em machines a cada check-in que o inclua no payload,
mesmo padrão de persistência já usado para mac_address/serial_number.

FR-005
Deve existir agent-windows/itcenter-agent-updater.ps1, executado por uma Tarefa Agendada
dedicada (ITCenterAgentUpdater), separada da Tarefa Agendada de coleta (ITCenterAgent), com
frequência própria configurável (padrão 24 horas).

FR-006
O updater deve comparar a versão instalada localmente (lida do itcenter-agent.ps1 já instalado,
via o mesmo padrão $script:AgentVersion) contra a versão do manifest remoto (consultado com o
próprio hostname da máquina, FR-001) antes de decidir se atualiza.

FR-007
Se o manifest retornar target_agent_version preenchido e diferente de version, o updater não
deve aplicar a atualização (hold-back) e deve logar o motivo — ver Business Rules sobre a
semântica exata desta trava.

FR-008
Antes de substituir o script instalado, o updater deve validar, sem nenhum fallback de bypass:
(a) Get-AuthenticodeSignature do arquivo baixado com Status -eq 'Valid'; (b) hash SHA-256 do
arquivo baixado igual ao valor retornado por /manifest. Falha em qualquer uma das duas invalida
a atualização (o arquivo baixado é descartado, nada é substituído, falha é logada).

FR-009
Antes de substituir o script instalado, o updater deve copiar o script atual para
itcenter-agent.ps1.previous. A substituição do script ativo deve ser atômica (Move-Item -Force).

FR-010
Após aplicar uma atualização, o updater deve registrar um estado de "atualização pendente de
confirmação" (ver Data Model) e não deve tratar a atualização como definitiva até o critério de
confirmação (FR-012) ou de rollback (FR-011) ser atingido.

FR-011
Se, após uma atualização aplicada, o número de check-ins de coleta consecutivos com falha
atingir o limite configurado (padrão 5), o updater deve, na próxima execução da sua própria
Tarefa Agendada, restaurar itcenter-agent.ps1.previous sobre o script ativo (mesma validação de
assinatura do arquivo restaurado, defesa em profundidade), atualizar o estado local e registrar
a falha e o rollback no log.

FR-012
Se, após uma atualização aplicada, o número de check-ins de coleta consecutivos com sucesso
atingir o limite configurado (padrão 3) antes do limite de falha do FR-011, o updater deve
marcar a atualização como confirmada e parar de rastreá-la (o arquivo .previous permanece em
disco até a próxima atualização, sem ser removido automaticamente).

FR-013
itcenter-agent.ps1 (coleta) deve, a cada execução, atualizar um contador local de check-ins
consecutivos com sucesso/falha usado pelo updater (FR-011/012) — apenas quando esse estado já
existir (criado pelo updater na primeira atualização); em máquinas nunca atualizadas
automaticamente, nenhum arquivo/comportamento novo é criado.

FR-014
install-agent.ps1 deve registrar a Tarefa Agendada ITCenterAgentUpdater (mesmo principal SYSTEM,
mesma política de ExecutionPolicy AllSigned/Bypass já aplicada à Tarefa Agendada de coleta).

FR-015
uninstall-agent.ps1 deve remover também a Tarefa Agendada ITCenterAgentUpdater (hoje só remove
ITCenterAgent).

FR-016
scripts/Sign-AgentScripts.ps1 deve assinar também itcenter-agent-updater.ps1 (hoje assina só os
3 scripts existentes).

FR-017
install-agent.ps1 deve validar a assinatura Authenticode de itcenter-agent-updater.ps1 antes de
copiá-lo para o InstallPath, mesmo padrão já aplicado aos 3 scripts existentes (Assert-
AgentScriptSignature), respeitando o mesmo fallback -SkipSignatureCheck só para instalação
local/dev (o fallback aqui é sobre a instalação do updater, não sobre a validação que o próprio
updater faz em runtime — essa nunca tem fallback, FR-008).

FR-018
GET /api/v1/machines e GET /api/v1/machines/{id} devem expor agent_version e
target_agent_version.

FR-019
MachineDetailView.tsx deve exibir agent_version no detalhe da máquina, mesmo padrão de
DetailItem já usado para mac_address/serial_number.

FR-020
docs/backend/API.md, docs/backend/DATABASE.md, docs/agent/CHECKIN.md e
docs/agent/INSTALLATION.md devem ser atualizados refletindo os itens acima.
```

## Inputs / Outputs

- `GET /api/v1/agent/manifest[?hostname=PC-FINANCEIRO-01]` → `200 {"version": "1.1.0", "sha256":
  "<64 hex chars>", "target_agent_version": null}` (ou o valor cadastrado, se `hostname` bater com
  uma máquina que tenha `target_agent_version` preenchido) ou `401`/`500` nas mesmas condições
  de sempre. `hostname` ausente ou sem correspondência → `target_agent_version: null`.
- `GET /api/v1/agent/download` → `200` com `Content-Type: application/octet-stream` e o corpo
  sendo os bytes do script, ou `401`/`500` nas mesmas condições acima.
- Payload de check-in (`POST /api/v1/agent/checkin`): ganha `agent_version: string | null`
  (opcional, mesmo padrão de `mac_address`/`serial_number` — ausência não bloqueia o check-in).
- `GET /api/v1/machines`, `GET /api/v1/machines/{id}`: ganham `agent_version` e
  `target_agent_version` na resposta.

## Data Model

```sql
-- machines.agent_version: versão do agente reportada pelo próprio agente a cada check-in.
ALTER TABLE machines ADD COLUMN agent_version VARCHAR(20) NULL;

-- machines.target_agent_version: trava opcional de rollout (ver Business Rules).
ALTER TABLE machines ADD COLUMN target_agent_version VARCHAR(20) NULL;
```

Estado local do updater (novo arquivo, não é dado do banco): `update-state.json`, no mesmo
`InstallPath` do agente (ex.: `C:\Program Files\ITCenterAgent\update-state.json`), com a mesma
ACL restrita a `SYSTEM`/`Administrators` já aplicada a `config.json` (`Protect-AgentPath`).

```json
{
  "applied_version": "1.1.0",
  "previous_version": "1.0.0",
  "updated_at": "2026-08-20T03:00:00Z",
  "consecutive_checkin_failures": 0,
  "consecutive_checkin_successes": 0
}
```

Ausência deste arquivo é o estado normal de uma máquina que nunca recebeu uma atualização
automática — nada no fluxo de coleta muda para ela.

## Business Rules

- **Origem do release servido pelo backend (resolve o gap não fechado pela ADR-032):** o backend
  passa a incluir, na sua própria imagem Docker, uma cópia assinada de `itcenter-agent.ps1` (só
  o script de coleta — não `install-agent.ps1`/`uninstall-agent.ps1`/testes). Isso exige mudar o
  build context do serviço `backend` em `infra/docker-compose.production.yml` de `../backend`
  para a raiz do repositório (`..`), com `dockerfile: backend/Dockerfile` explícito, para que o
  `Dockerfile` possa copiar `agent-windows/itcenter-agent.ps1` para dentro da imagem (ex.:
  `/app/agent-release/itcenter-agent.ps1`). A versão publicada (`/manifest`) é extraída por regex
  da linha `$script:AgentVersion = "..."` do próprio arquivo copiado (fonte única de verdade —
  nunca um número declarado separadamente que possa divergir do arquivo real); o hash SHA-256 é
  calculado sobre os bytes desse mesmo arquivo. **Publicar uma nova versão do agente = editar
  `$script:AgentVersion`, assinar com `Sign-AgentScripts.ps1`, e fazer o próximo deploy de
  produção do backend** — sem infraestrutura nova (sem bucket, sem tabela de binário), mas o
  ciclo de release do agente fica acoplado ao ciclo de deploy do backend.
- **`target_agent_version` é uma trava de "não atualizar", não um "envie-me esta versão
  específica do passado":** como o backend só guarda a versão atualmente publicada (não um
  histórico), não é possível mandar uma máquina para uma versão arbitrária anterior que não seja
  a que ela já tem instalada. Nesta implementação: se `target_agent_version` estiver preenchido e
  for diferente da versão do manifest, o updater simplesmente não atualiza aquela máquina
  (permanece na versão já instalada) — útil para segurar uma máquina específica fora de um
  rollout, não para fazer canário forward controlado por versão exata. Ampliar isso para um
  rollout canário completo exigiria o backend guardar múltiplos releases, fora de escopo aqui.
- **Endpoints `/manifest` e `/download` usam só `X-Agent-Api-Key`** (autenticação de classe, mesma
  do check-in) — não o `agent_secret` por máquina do ADR-036, porque não servem dado específico
  de uma máquina (o mesmo script/manifest vale para toda a frota).
- **O updater nunca aceita bypass de assinatura/hash em runtime** (diferente do instalador, que
  tem `-SkipSignatureCheck` só para uso local/dev) — se a validação falhar, o arquivo baixado é
  descartado e nada é substituído.
- **A janela de detecção de rollback é limitada pela frequência do updater**, não é instantânea:
  como a Tarefa Agendada do updater roda no padrão 1x/dia, uma atualização ruim pode continuar
  ativa por até um ciclo do updater antes do rollback automático disparar (o ciclo de coleta
  continua rodando/cacheando localmente nesse meio-tempo, mas sem sucesso se a atualização
  quebrou o check-in). Mitigação disponível: reduzir `updater_interval_hours` no `config.json`, ou
  rollback manual (rodar o updater manualmente, ou reinstalar) se o operador perceber antes via
  `agent_version`/status "offline" no dashboard.
- **`agent_version` é apenas informativo/observabilidade** — nenhuma regra SOC ou alerta é gerada
  a partir dele nesta EPIC (fora de escopo; nada no backlog pede isso).

## State / Behavior

```
Updater (ITCenterAgentUpdater, roda a cada updater_interval_hours):
  1. Ler update-state.json local, se existir.
  2. Se existir estado pendente (applied_version setado, não confirmado nem já revertido):
     a. Se consecutive_checkin_failures >= limite de rollback (padrão 5) -> ROLLBACK
        (restaura .previous, valida assinatura do restaurado, zera estado, loga).
     b. Senão se consecutive_checkin_successes >= limite de confirmação (padrão 3) ->
        CONFIRMA (marca applied_version como definitivo, limpa o "pendente").
     c. Senão -> segue aguardando (nenhuma ação).
  3. Consultar GET /api/v1/agent/manifest?hostname=<hostname da própria máquina>.
  4. Comparar $script:AgentVersion local vs manifest.version.
     - Igual -> nada a fazer.
     - Diferente e manifest.target_agent_version preenchido e != manifest.version -> HOLD-BACK,
       loga e para.
     - Diferente (sem trava) -> baixar via GET /api/v1/agent/download, validar assinatura+hash
       (FR-008), se válido: backup (.previous) + substituição atômica + grava novo
       update-state.json (applied_version = manifest.version, contadores zerados).

Coleta (ITCenterAgent, a cada checkin_interval_minutes):
  fluxo de check-in já existente, sem mudança de comportamento —
  só ganha, ao final (sucesso ou falha classificada), UM passo novo:
  se update-state.json existir, incrementa consecutive_checkin_successes (e zera
  consecutive_checkin_failures) em caso de sucesso, ou incrementa
  consecutive_checkin_failures (e zera consecutive_checkin_successes) em caso de falha.
```

## Error Handling

- Manifest/download sem `X-Agent-Api-Key` válido → `401`, mesmo formato de erro do check-in.
- Backend sem nenhuma versão publicada configurada (falha de deploy/imagem) → `500` claro nos
  dois endpoints, nunca uma resposta parcial/ambígua.
- Download com assinatura inválida ou hash divergente → updater descarta o arquivo temporário,
  loga `ERROR` com o motivo específico (assinatura vs. hash), não altera nada em disco, tenta de
  novo apenas no próximo ciclo agendado (sem retry imediato — mesmo espírito de não gerar tráfego
  desnecessário já usado para o check-in).
- Falha de rede ao contatar manifest/download → tratada como falha temporária, mesma classificação
  de erro já usada em `Send-PendingAgentCheckins` (não interrompe a Tarefa Agendada, só não
  atualiza neste ciclo).
- `update-state.json` corrompido/ilegível → tratado como "sem estado pendente" (mesma filosofia de
  resiliência do resto do agente: nunca travar por um arquivo de estado ruim); logado como `WARN`.

## Edge Cases

- Máquina que nunca recebeu atualização automática: sem `update-state.json`, sem nenhuma mudança
  de comportamento na coleta.
- Duas atualizações aplicadas em sequência antes de uma confirmar (updater rodou, atualizou;
  antes de confirmar/reverter, uma nova versão aparece no manifest): a spec não cobre encadear
  updates sobre um update ainda não confirmado — o updater deve esperar o estado atual resolver
  (confirmar ou reverter) antes de considerar uma nova versão, para não perder o ponto de
  rollback correto.
- `target_agent_version` setado para um valor que nunca existiu/não bate com nada: tratado igual
  a "diferente do manifest" → hold-back (comportamento seguro por padrão).
- Rollback restaura `.previous`, mas `.previous` também falha em contatar a API (ex.: problema de
  rede, não da atualização em si): fora do controle do updater — o rollback já devolveu a última
  versão conhecida-boa; o problema de conectividade é responsabilidade do runbook operacional
  existente, não desta feature.

## Security Requirements

- **Modelo de ameaça principal:** um manifest/download comprometido (backend invadido, ou imagem
  Docker alterada) é equivalente a execução de código arbitrário como `SYSTEM` em toda a frota.
  A defesa é a mesma da ADR-031 (assinatura Authenticode obrigatória, verificada contra o
  certificado já confiável na máquina) **mais** o hash SHA-256 do manifest — as duas camadas são
  independentes (um atacante precisaria comprometer tanto o backend quanto a chave privada de
  assinatura, que nunca fica no backend/repositório).
- `X-Agent-Api-Key` é a única autenticação dos 2 endpoints novos — consistente com o check-in,
  mas vale registrar: qualquer processo que já tenha essa chave (ex.: uma máquina já comprometida,
  ver ADR-036) pode consultar manifest/download; isso não piora o risco existente (a chave já dá
  acesso de escrita a check-in), mas também não é uma barreira adicional — a barreira real contra
  atualização maliciosa é a assinatura de código, não a API key.
- Nenhum dado sensível novo trafega nesses 2 endpoints (script público do agente + hash).
- `update-state.json` não contém segredo algum (só versões/contadores/timestamp) — ACL restrita
  é defesa em profundidade contra adulteração local (um usuário não-admin forjando confirmação/
  rollback), não proteção de confidencialidade.
- Sem mudança nenhuma na autenticação de usuários humanos (RBAC, login) — este é território só
  de autenticação de agente.

## Non-Functional Requirements

- O updater não deve rodar com frequência maior que a coleta (constraint explícita da ADR-032) —
  padrão 24h vs. 5min da coleta.
- Sem dependência de terceiro nova em nenhum dos dois lados (backend: só stdlib
  `hashlib`/`re`; agente: só cmdlets nativos do PowerShell 5.1, mesmo padrão do resto do agente).
- Download não deve crescer o tempo de resposta HTTP significativamente — o script de coleta tem
  poucos KB, sem necessidade de streaming/chunking.

## Acceptance Criteria

```
Scenario: Manifest retorna a versão publicada
Given o backend está publicado com itcenter-agent.ps1 versão "1.1.0" assinado
When um cliente chama GET /api/v1/agent/manifest com X-Agent-Api-Key válido
Then a resposta é 200 com {"version": "1.1.0", "sha256": "<hash real do arquivo>"}

Scenario: Download serve exatamente o arquivo do manifest
Given o manifest retornou sha256 X para a versão atual
When um cliente chama GET /api/v1/agent/download com a mesma X-Agent-Api-Key
Then o corpo da resposta, quando hasheado em SHA-256, é igual a X

Scenario: Updater aplica atualização válida
Given a máquina tem itcenter-agent.ps1 versão "1.0.0" instalado e sem target_agent_version
And o manifest remoto anuncia versão "1.1.0" com assinatura e hash válidos
When itcenter-agent-updater.ps1 roda
Then itcenter-agent.ps1.previous contém a versão "1.0.0"
And itcenter-agent.ps1 ativo contém a versão "1.1.0"
And update-state.json registra applied_version "1.1.0", previous_version "1.0.0", contadores zerados

Scenario: Updater rejeita atualização com assinatura inválida
Given o manifest remoto anuncia uma versão nova
And o arquivo baixado não tem Get-AuthenticodeSignature Status "Valid"
When itcenter-agent-updater.ps1 roda
Then nenhum arquivo em disco é substituído
And um erro é registrado no log mencionando falha de assinatura

Scenario: Updater rejeita atualização com hash divergente
Given o arquivo baixado tem assinatura válida mas sha256 diferente do manifest
When itcenter-agent-updater.ps1 roda
Then nenhum arquivo em disco é substituído
And um erro é registrado no log mencionando divergência de hash

Scenario: Auto-rollback após falhas consecutivas pós-atualização
Given uma atualização foi aplicada e update-state.json tem applied_version pendente
And o agente de coleta registrou 5 check-ins consecutivos com falha desde a atualização
When itcenter-agent-updater.ps1 roda novamente
Then itcenter-agent.ps1 ativo volta a ser a versão registrada em previous_version
And update-state.json reflete o rollback
And um evento de rollback é registrado no log

Scenario: Atualização confirmada após sucessos consecutivos
Given uma atualização foi aplicada e update-state.json tem applied_version pendente
And o agente de coleta registrou 3 check-ins consecutivos com sucesso desde a atualização
When itcenter-agent-updater.ps1 roda novamente
Then update-state.json deixa de marcar a atualização como pendente
And nenhum rollback ocorre

Scenario: target_agent_version segura uma máquina fora do rollout
Given machines.target_agent_version = "1.0.0" para o hostname desta máquina
And GET /api/v1/agent/manifest?hostname=<hostname> retorna version "1.1.0" e
    target_agent_version "1.0.0"
When itcenter-agent-updater.ps1 roda
Then nenhuma atualização é baixada nem aplicada
And o log registra o motivo (hold-back por target_agent_version)

Scenario: Máquina nunca atualizada automaticamente não muda de comportamento
Given update-state.json não existe para esta máquina
When itcenter-agent.ps1 roda um ciclo normal de check-in
Then nenhum arquivo de estado de atualização é criado
And o comportamento de check-in é idêntico ao anterior a esta EPIC

Scenario: agent_version aparece no dashboard
Given uma máquina reportou agent_version "1.1.0" no último check-in
When um usuário autenticado abre o detalhe dessa máquina no dashboard
Then o campo "Versão do Agente" (ou label equivalente) exibe "1.1.0"
```

## Constraints

- Sem dependências externas novas em nenhum lado (ADR-005/ADR-025).
- Sem Serviço Windows via SCM/NSSM/WinSW (ADR-032).
- Updater nunca aceita fallback de bypass de assinatura/hash em runtime (ADR-032, diferente do
  instalador).
- Sem mudança de schema do payload de check-in além do campo aditivo `agent_version`.
- Migrations aditivas, colunas `NULL`-able, forward-only (padrão já usado nas 12 migrations
  existentes).

## Assumptions

- **Origem do release do agente = imagem Docker do backend (Option A da pesquisa).** Assumido
  porque é a opção que não introduz infraestrutura nova (sem bucket, sem tabela de binário, sem
  runbook manual de cópia de arquivo na VM) e mantém uma única fonte de verdade (o próprio arquivo
  assinado). Trade-off aceito conscientemente: publicar uma nova versão do agente passa a exigir
  um deploy de backend. **Esta é a decisão de maior impacto de infraestrutura desta spec — envolve
  mudar o build context do serviço `backend` em `infra/docker-compose.production.yml`.** Se essa
  premissa estiver errada (ex.: preferência por desacoplar o release do agente do deploy do
  backend), avisar antes da fase de implementação — é reversível agora, mais custoso depois de
  implementado.
- **Escrita de `target_agent_version` fica fora desta EPIC** (só SQL manual), porque o backlog
  registrado em `docs/development/TASKS.md` não lista nenhum endpoint/UI para isso — só a coluna
  e a leitura pelo updater.
- **Limite de rollback = 5 falhas consecutivas, limite de confirmação = 3 sucessos consecutivos.**
  Proposto porque a ADR-032 deixou o número exato "a definir na implementação"; 5 falhas com
  `checkin_interval_minutes` padrão de 5 min ≈ 25 min de janela — suficiente para distinguir de
  uma falha temporária isolada (já tratada pelo retry por request existente) sem demorar demais
  para reagir a uma atualização realmente quebrada.
- **Frequência padrão do updater = 24 horas**, conforme sugestão explícita da ADR-032.
- **`update-state.json` é um arquivo novo, não uma tabela nova no banco** — decisão consistente
  com o restante do agente (estado local em arquivo, não em banco; o banco só recebe
  `agent_version` via check-in, que é informativo).

## Open Questions

Nenhuma pergunta bloqueante remanescente — o usuário aprovou a spec nesta sessão. As Assumptions
acima documentam as decisões de design que a ADR-032/backlog deixaram em aberto; a de maior
impacto (origem do release na imagem Docker do backend) fica destacada para reconfirmação rápida
antes de tocar em `infra/docker-compose.production.yml`, dado que é a única com custo real de
reverter depois de implementada.
