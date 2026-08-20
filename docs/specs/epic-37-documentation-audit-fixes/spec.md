# Spec: EPIC 37 - Correção de Achados da Auditoria de Documentação (2026-08-19)

## Metadata

- Status: VERIFIED (ver verification.md) — Trilha 1 verificada localmente, não deployada em produção
- Nível de rigor: 3 (arquitetural) — a Trilha 1 muda uma fronteira de autenticação em
  produção (o que passa ou não pelo Basic Auth do Nginx), o que por si só já justifica o
  nível 3 mesmo as Trilhas 2 e 3 sendo mais simples isoladamente.
- Autor/origem: achados da auditoria de documentação de 2026-08-19 (`docs/development/
  TASKS.md`, EPIC 37) + `/sdd` (sessão 2026-08-19)
- Data: 2026-08-19
- Dependências: EPIC 22 (ADR-032, endpoints `/agent/manifest`/`/agent/download` — Trilha 1),
  EPIC 30 (migration 011 — Trilha 2, ainda não commitada), EPIC 28-B (padrão de validação
  manual de mudança de Nginx — Trilha 1)

## Context

Uma auditoria de documentação encontrou 3 divergências entre docs e código que não eram só
texto desatualizado, mas bugs/gaps reais: (1) o Nginx de produção não libera os 2 endpoints
novos do updater do Basic Auth, bloqueando a auto-atualização do agente; (2) uma migration
ainda não commitada vai causar crash-loop do backend a cada restart assim que for deployada;
(3) duas regras SOC (VPN/Torrent) não cobrem `processes`, ao contrário do que a política
documentada dizia (já corrigida no texto pela própria auditoria).

## Goal

As 3 divergências deixam de existir: o updater funciona atrás do Nginx real, a migration 011
sobrevive a reaplicações, e a cobertura de VPN/Torrent bate com o que for decidido (estender
ou aceitar a limitação, mas de forma explícita, não por omissão).

## Scope

- Trilha 1: novo bloco `location` em `infra/nginx/nginx.conf.template` para
  `/api/v1/agent/manifest` e `/api/v1/agent/download`.
- Trilha 2: correção in-place de `backend/migrations/011_installed_programs_publisher_unique.sql`
  para ser idempotente.
- Trilha 3: decisão explícita (usuário) entre estender `_process_software_value()` para
  cobrir `UNAUTHORIZED_VPN_TOOLS`/`TORRENT_TOOLS` também em `payload.processes`, ou manter a
  limitação atual como aceita conscientemente — e implementação da opção escolhida.
- Atualizar `docs/deployment/KNOWN_ISSUES.md`, `docs/security/ASSET_POLICY.md`,
  `docs/architecture/SECURITY.md`, `docs/security/AUTH.md` e `docs/security/SECURITY.md`
  removendo as notas de "gap conhecido" conforme cada trilha for corrigida.

## Out of Scope

- Tabela de controle de migrations / testar idempotência de `apply_migrations()` de forma
  geral — já é a EPIC 33, não esta.
- Decidir a estratégia do gate de CVE do Docker Scout — EPIC 36, não esta.
- Qualquer mudança de RBAC, autenticação humana ou `agent_secret` (ADR-036) — a Trilha 1 é
  só sobre o Nginx deixar a chamada chegar ao FastAPI, a autenticação em si (`X-Agent-Api-Key`)
  não muda.
- Rate limiting novo para `/agent/manifest`/`/agent/download` além do que for decidido na
  Open Question 2 — sem exigência concreta de limite específico ainda.

## Functional Requirements

```
FR-001 (Trilha 1)
O Nginx de produção deve encaminhar GET /api/v1/agent/manifest e GET /api/v1/agent/download
para o backend sem exigir HTTP Basic Auth, mesmo padrão já aplicado a
POST /api/v1/agent/checkin.

FR-002 (Trilha 1)
O bloco novo deve repassar X-Agent-Api-Key e os mesmos headers de proxy já usados no bloco
de /agent/checkin (Host, X-Real-IP, X-Forwarded-For, X-Forwarded-Proto), para que
request_ip() (backend/app/services/auth.py) continue recebendo o IP real caso esses
endpoints um dia precisem dessa informação.

FR-003 (Trilha 2)
A migration 011_installed_programs_publisher_unique.sql deve poder ser aplicada duas vezes
seguidas contra o mesmo banco sem erro, mesmo padrão de idempotência já usado nas migrations
009/010/012.

FR-004 (Trilha 2)
A correção deve ser feita no próprio arquivo 011 (não uma migration nova), porque 011 ainda
não foi commitada nem aplicada em nenhum ambiente além de bancos de teste locais descartáveis.

FR-005 (Trilha 3 - condicional a Open Question 1)
Se a decisão for estender a cobertura: o backend deve avaliar
UNAUTHORIZED_VPN_TOOLS/TORRENT_TOOLS também contra cada valor de payload.processes, com o
mesmo dedup via seen_detections já usado para as outras 4 categorias e para
installed_programs, gerando os mesmos eventos (unauthorized_vpn_tool/
torrent_software_detected) com a mesma severidade (high) já documentada.

FR-006 (Trilha 3 - condicional a Open Question 1)
Se a decisão for manter a limitação: nenhuma mudança de código é feita; a nota já adicionada
em docs/security/ASSET_POLICY.md (2026-08-19) deixa de ser tratada como "gap conhecido" e
passa a ser a descrição definitiva do comportamento.
```

## Inputs / Outputs

- Trilha 1: sem mudança de contrato HTTP (mesmos 2 endpoints já existentes, EPIC 22) — só a
  camada de rede (Nginx) passa a deixar a requisição chegar ao FastAPI.
- Trilha 2: sem input/output novo — mesma migration, resultado final idêntico
  (`installed_programs_machine_name_version_publisher_unique` como única constraint ativa).
- Trilha 3 (se estendida): nenhum campo novo no payload; `processes` já existe e já é
  avaliado para as outras 4 categorias. O evento gerado (`unauthorized_vpn_tool`/
  `torrent_software_detected`) ganha `raw_data` no formato de `_software_detection_raw_data()`
  (mesmo formato das outras 4 categorias) em vez de `program.model_dump()` — muda o formato
  interno de `raw_data` para VPN/Torrent mesmo quando disparado por `installed_programs`
  (efeito colateral da unificação via `_process_software_value()`, ver Business Rules).

## Data Model

Nenhuma mudança de schema. Trilha 2 é a única que toca definição de banco, e o resultado
final (constraint `UNIQUE (machine_id, name, version, publisher)`) já é exatamente o que a
migration 011 original pretendia — só a idempotência da aplicação muda.

## Business Rules

- **Trilha 1**: o bloco novo não deve ter `limit_req zone=agent_checkins` (esse limite foi
  dimensionado para o volume de check-in, a cada poucos minutos por máquina; manifest/download
  são consultados 1x/dia pelo updater) — ver Open Question 2 sobre se algum rate limit próprio
  é desejado.
- **Trilha 3, se estendida**: mover os 2 loops de `UNAUTHORIZED_VPN_TOOLS`/`TORRENT_TOOLS`
  para dentro de `_process_software_value()` (em vez de inline no loop de
  `installed_programs`) é a forma de estender a cobertura reaproveitando a função já
  compartilhada com `processes` — consequência: o `raw_data` desses 2 eventos passa a usar
  `_software_detection_raw_data(tool_name=..., matched_value=..., category=..., source_field=...,
  extra=...)` em vez de `program.model_dump()` diretamente. Isso é uma mudança de formato
  interno de `raw_data` (campo JSONB, sem contrato de API público sobre seu formato exato) —
  não é uma breaking change de API, mas vale confirmar que nenhum consumidor (dashboard,
  relatório) depende do formato antigo de `raw_data` desses 2 eventos especificamente antes de
  implementar.

## State / Behavior

Nenhuma mudança de estado/máquina de estados nas 3 trilhas — são correções pontuais de
comportamento já existente, não fluxos novos.

## Error Handling

- Trilha 1: sem mudança nos códigos de erro do FastAPI (401 por API key ausente/errada, 500
  por release não configurado, já existentes desde a EPIC 22) — o Nginx simplesmente passa a
  deixar a requisição chegar até esse ponto.
- Trilha 2: `apply_migrations.py` deve continuar tratando a segunda aplicação da migration
  011 como no-op bem-sucedido (mesmo comportamento das demais migrations idempotentes), não
  como erro.
- Trilha 3: sem mudança de tratamento de erro — mesma tolerância a payload malformado já
  existente em `_process_software_value`/`process_installed_program_rules`.

## Edge Cases

- Trilha 1: um agente ainda não atualizado (sem `agent-windows/itcenter-agent-updater.ps1`,
  versões anteriores à EPIC 22) nunca chama `/manifest`/`/download` — a mudança não afeta
  esses agentes.
- Trilha 2: um banco que já tenha a constraint antiga
  (`installed_programs_machine_name_version_unique`) removida manualmente (cenário raro, só
  em bancos de teste manipulados à mão) — a correção deve continuar segura mesmo nesse caso
  (`DROP CONSTRAINT IF EXISTS` não falha se a constraint já não existir).
- Trilha 3, se estendida: um processo cujo nome coincida por substring com um termo de
  `UNAUTHORIZED_VPN_TOOLS`/`TORRENT_TOOLS` mas não seja a ferramenta real (mesmo risco de
  falso positivo por substring que já existe hoje para as outras 4 categorias — não é uma
  regressão nova, é o mesmo trade-off já aceito no projeto).

## Security Requirements

- **Trilha 1 é, por definição, uma mudança de fronteira de autenticação em produção** — exige
  confirmação humana explícita antes de aplicar contra a VM real (não só revisão de código),
  consistente com "Human-in-the-loop obrigatório" do skill. Validar que a mudança **não**
  abre acidentalmente nada além dos 2 paths pretendidos (o bloco deve usar `location =`
  igual ao existente, correspondência exata, não `location ^~` ou regex que poderia
  capturar mais do que o esperado).
- Nenhuma das 3 trilhas expõe dado novo, remove autenticação existente ou muda RBAC.
- Trilha 3 (se estendida) é uma ampliação de detecção (mais visibilidade, não menos) —
  sem risco de segurança novo, só efeito colateral de formato de `raw_data` (ver Business
  Rules).

## Non-Functional Requirements

- Trilha 1: sem regressão de performance esperada — mesmo padrão de proxy já usado nos
  outros blocos.
- Trilha 3 (se estendida): custo adicional é 2 loops (`len(UNAUTHORIZED_VPN_TOOLS)` +
  `len(TORRENT_TOOLS)`, 4 + 3 = 7 comparações de substring) por processo em execução —
  desprezível dado o volume atual (parque pequeno, poucos processos por check-in).

## Acceptance Criteria

```
Scenario: Manifest acessível atrás do Nginx sem Basic Auth
Given o Nginx de produção com o bloco novo aplicado
When um cliente chama GET /api/v1/agent/manifest com X-Agent-Api-Key válido, sem enviar
    Authorization: Basic
Then a resposta é 200 (ou o código que o backend já retornaria), nunca 401 do proprio Nginx

Scenario: Download acessível atrás do Nginx sem Basic Auth
Given o Nginx de produção com o bloco novo aplicado
When um cliente chama GET /api/v1/agent/download com X-Agent-Api-Key válido, sem enviar
    Authorization: Basic
Then a resposta é 200 com os bytes do script, nunca 401 do proprio Nginx

Scenario: Dashboard e demais rotas continuam exigindo Basic Auth
Given o Nginx de producao com o bloco novo aplicado
When um cliente acessa a raiz do dashboard sem Authorization: Basic
Then a resposta continua sendo 401 (comportamento inalterado para as demais rotas)

Scenario: Migration 011 sobrevive a reaplicacao
Given um banco Postgres com a migration 011 ja aplicada com sucesso uma vez
When apply_migrations.py roda novamente (reaplicando todos os arquivos, comportamento atual)
Then nenhum erro ocorre e o backend sobe normalmente

Scenario: Constraint final identica independente de quantas vezes a migration rodar
Given a migration 011 corrigida
When aplicada 1 vez ou N vezes seguidas contra o mesmo banco
Then a unica constraint ativa em installed_programs para (machine_id, name, version,
    publisher) e installed_programs_machine_name_version_publisher_unique, sem duplicatas
    nem erro

Scenario: [Trilha 3, se estendida] VPN nao autorizada detectada via processo em execucao
Given um payload de check-in com "hamachi.exe" em processes e ausente de installed_programs
When o check-in e processado
Then um security_event unauthorized_vpn_tool e um alerta high sao gerados, mesmo padrao ja
    aplicado quando a ferramenta aparece em installed_programs

Scenario: [Trilha 3, se mantida a limitacao] Nenhuma mudanca de comportamento
Given a decisao de manter a limitacao atual
When um payload de check-in trouxer uma VPN nao autorizada so em processes
Then nenhum evento e gerado (comportamento atual preservado), e
    docs/security/ASSET_POLICY.md descreve isso como comportamento definitivo, nao mais como
    gap conhecido
```

## Constraints

- Nenhuma tecnologia nova em nenhuma das 3 trilhas.
- Trilha 2 não pode ser uma migration nova (`012`/`013` já existem para outros fins) — a
  correção é in-place no arquivo `011`, permitido só porque nunca foi commitado/deployado.
- Trilha 1 não deve alterar nenhum outro bloco `location` existente.

## Assumptions

- **Trilha 1 não recebe `limit_req` próprio nesta correção** — assumido que o volume de
  manifest/download (1x/dia por máquina, updater) não justifica rate limit dedicado agora;
  revisitar se abuso real for observado. Ver Open Question 2 para confirmação.
- **Trilha 2 é corrigida in-place**, não via nova migration — seguro porque `011` nunca foi
  commitada (confirmado via `git status`).

## Open Questions

Respondidas pelo usuário em 2026-08-19:

1. **Trilha 3**: estender `UNAUTHORIZED_VPN_TOOLS`/`TORRENT_TOOLS` para cobrir
   `payload.processes` — **decisão: estender** (FR-005 vale; FR-006 descartada).
2. **Trilha 1**: manifest/download sem `limit_req` próprio — **decisão: sem rate limit
   próprio** (confirma a Assumption já registrada acima).

Nenhuma pergunta em aberto restante. Spec pronta para implementação das 3 trilhas.
