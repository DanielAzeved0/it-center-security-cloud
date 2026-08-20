# Spec: EPIC 31 — Resiliência do Agente Windows

## Metadata

- Status: **SPECIFIED** (não aprovada ainda — ver Open Questions antes de virar APPROVED)
- Nível de rigor: 2 (hardening pontual em componente existente, sem mudança de arquitetura/
  contrato entre agente-API-dashboard)
- Autor/origem: auditoria técnica 2026-08-15, EPIC 31 de `docs/development/TASKS.md`
- Data: 2026-08-17
- Dependências: nenhuma migration/endpoint novo; reassinatura do agente (ADR-031) antes do
  deploy real

## Context

A auditoria técnica de 2026-08-15 encontrou 4 gaps de resiliência em
`agent-windows/itcenter-agent.ps1` que podem fazer uma máquina sumir do dashboard sem estar
genuinamente offline, reportar identidade errada, perder itens da fila de reenvio sob
concorrência, ou reportar o IP de uma rede virtual em vez da rede real — tudo isso sem
nenhum log de erro visível que aponte a causa raiz. `research.md` confirma os 4 achados
linha a linha no código atual.

## Goal

Fechar os 4 gaps mantendo a mesma filosofia de resiliência já aplicada no restante do
agente (EPIC 16): falha em uma coleta nunca derruba o check-in inteiro, e comportamento
inesperado sempre vira log, nunca exceção silenciosa ou dado incorreto sem aviso.

## Scope

- Try/catch dedicado em `Get-AgentLocalAdmins`.
- Nova fonte primária de usuário em `Get-AgentUsername` (usuário do console interativo),
  com fallback explícito.
- Lock (mutex) ao redor de `Send-PendingAgentCheckins`.
- Exclusão de adaptadores virtuais/VPN conhecidos na seleção de IP em
  `Get-AgentNetworkInfo`.
- Testes novos em `agent-windows/tests/run-agent-tests.ps1` cobrindo os 4 comportamentos.
- Atualização de `docs/agent/TROUBLESHOOTING.md` (novos comportamentos) e
  `docs/agent/CHECKIN.md` (semântica de `username` muda de "identidade do processo" para
  "usuário do console interativo, com fallback").

## Out of Scope

- Trocar o principal da Tarefa Agendada de `SYSTEM` para outro usuário (quebraria o modelo
  de privilégio já validado; a correção do item de usuário é só no coletor).
- Qualquer mudança de contrato de API/schema do check-in (o campo `username` já existe e
  continua com o mesmo nome/tipo — só a fonte do valor muda).
- Identidade individual por agente / revogação de agente comprometido (isso é a EPIC 28,
  achado de personificação de máquina — não misturar aqui).
- Resolver o achado de path traversal do proxy ou os demais itens das EPICs 28-30/32/33.

## Functional Requirements

```
FR-001
Get-AgentSecurityPayload deve continuar retornando local_admins mesmo quando
Get-AgentLocalAdmins encontrar um membro do grupo Administradores cujo SID não resolve
para nome. Nesse caso, a função deve logar um WARN e retornar a lista de admins que
conseguiu resolver (ou lista vazia, se nenhum resolver), nunca propagar exceção.

FR-002
Get-AgentUsername deve tentar, nesta ordem: (1) usuário dono do processo interativo do
console (ex.: proprietário de explorer.exe, ou equivalente via
Win32_ComputerSystem.UserName/Get-CimInstance), (2) se não houver sessão interativa
(máquina sem ninguém logado), fallback para a identidade atual do processo (comportamento
de hoje), com um log INFO indicando qual fonte foi usada.

FR-003
Send-PendingAgentCheckins deve adquirir um lock exclusivo (Mutex nomeado, escopo Local\)
antes de iterar o diretório de cache. Se o lock já estiver em uso por outra execução, a
função deve retornar imediatamente (0 enviados) e logar INFO "outra execução já está
processando o cache pendente", sem esperar indefinidamente.

FR-004
Get-AgentNetworkInfo deve excluir da seleção adaptadores cuja descrição bata com uma lista
conhecida de adaptadores virtuais/VPN/tunelamento (ver Data Model) antes de ordenar por
InterfaceMetric. Se, após excluir, nenhum adaptador físico for encontrado, deve cair para o
comportamento atual (sem exclusão) e logar WARN "nenhum adaptador físico encontrado, usando
candidato sem filtro de virtualização" — nunca ficar sem IP quando existia algum candidato
antes do filtro.
```

## Inputs / Outputs

Sem mudança de schema do payload de check-in (`docs/agent/CHECKIN.md`): os campos
`local_admins`, `username`, `ip_address` continuam com o mesmo nome/tipo. Muda apenas como
o valor é obtido internamente no agente.

## Data Model

Lista inicial de substrings de descrição de adaptador a excluir (case-insensitive,
`-notlike`), proposta como ponto de partida — ver Open Questions:

```
*Hyper-V Virtual Ethernet*
*vEthernet*
*Virtual*
*VPN*
*TAP-Windows*
*WireGuard*
*Tailscale*
*ZeroTier*
*Hamachi*
*Radmin VPN*
*VMware Virtual*
*VirtualBox Host-Only*
*Windows Subsystem for Linux*
*Docker*
*Npcap*
*Loopback*
```

Manter como array no topo do script (`$script:VirtualAdapterPatterns` ou similar), não
hardcoded inline, para ser extensível sem precisar mexer na lógica.

## Business Rules

- Nenhum dos 4 fixes pode fazer o check-in falhar mais do que falha hoje — toda mudança é
  estritamente "mais tolerante a falha", nunca mais frágil.
- O lock (FR-003) é sobre o *envio do cache pendente*, não sobre o ciclo de coleta
  principal — não introduzir lock global que serialize o check-in inteiro.

## State / Behavior

N/A (sem máquina de estados nova; comportamento é ajuste pontual dentro do ciclo de
check-in já existente).

## Error Handling

- FR-001: exceção de `Get-LocalGroupMember` → log WARN, função retorna o que conseguiu
  coletar (nunca propaga).
- FR-002: nenhuma fonte de usuário disponível → mesmo comportamento de erro que existe hoje
  (`throw "Unable to collect username."` já existe na função — mantido como último recurso).
- FR-003: lock ocupado → log INFO, retorno `0`, sem exceção.
- FR-004: nenhum adaptador físico após filtro → log WARN, fallback para lógica atual
  (não é um erro, é um caso esperado em máquinas só com adaptador virtual).

## Edge Cases

- Máquina sem sessão interativa nenhuma (servidor headless) → FR-002 cai no fallback do
  processo, sem loop infinito nem exceção.
- Duas execuções manuais simultâneas de `Send-PendingAgentCheckins` (não só agendada vs.
  manual) → a segunda desiste rápido em vez de correr risco de `Remove-Item` duplicado.
- Máquina com múltiplos SIDs órfãos no grupo Administradores → FR-001 ainda retorna os
  admins válidos, não zera a lista inteira por causa de um SID quebrado.
- Máquina só com adaptador Hyper-V/WSL ativo (sem NIC física) → FR-004 não deixa a máquina
  sem IP reportado.

## Security Requirements

Nenhuma mudança de superfície de auth/dados sensíveis. FR-002 muda *quem* aparece como
`username` no payload (informação já coletada e exibida hoje, não uma exposição nova).

## Non-Functional Requirements

- FR-003 não pode introduzir espera longa: timeout do lock deve ser curto (ex.: alguns
  segundos) — a intenção é evitar corrida, não serializar execuções manuais indefinidamente.

## Acceptance Criteria

```
Scenario: admin com SID órfão não derruba o check-in
Given o grupo Administradores local tem um membro cujo SID não resolve para nome
When o agente roda o ciclo de coleta
Then Get-AgentSecurityPayload retorna local_admins com os nomes que resolveram
And o check-in continua normalmente (payload é montado e enviado/cacheado)
And um WARN é registrado no log

Scenario: check-in em produção reporta o usuário do console, não SYSTEM
Given a Tarefa Agendada roda com principal SYSTEM
And existe um usuário com sessão interativa ativa no console
When o agente coleta o username
Then o payload reporta o usuário do console, não "NT AUTHORITY\SYSTEM"

Scenario: máquina sem sessão interativa ainda reporta um username
Given não há nenhuma sessão de console ativa
When o agente coleta o username
Then o payload reporta a identidade do processo (comportamento atual), sem erro

Scenario: execução concorrente do reenvio de cache não perde arquivos
Given uma execução de Send-PendingAgentCheckins já está em andamento
When uma segunda execução (manual ou agendada) inicia
Then a segunda retorna imediatamente sem processar arquivos
And nenhum arquivo de cache é perdido ou duplicado

Scenario: adaptador virtual não é escolhido quando existe NIC física
Given a máquina tem um adaptador Hyper-V/VPN com métrica mais baixa que a NIC física
When o agente seleciona o IP
Then o IP reportado é o da NIC física, não do adaptador virtual

Scenario: máquina só com adaptador virtual ainda reporta um IP
Given a máquina não tem nenhum adaptador físico ativo, só virtual
When o agente seleciona o IP
Then o IP do adaptador virtual é reportado (fallback) com um WARN no log, em vez de IP nulo
```

## Constraints

- Sem dependências externas novas (ADR-005/ADR-025): mutex via `System.Threading.Mutex` do
  BCL, nada de módulo de terceiro.
- Scripts assinados (ADR-031): qualquer edição exige re-assinatura antes de deploy real.
- Sem mudança de schema do payload de check-in.

## Assumptions

- A lista de substrings de adaptador virtual (Data Model) é um ponto de partida razoável
  baseado em ferramentas já rastreadas em `ASSET_POLICY.md` + adaptadores de virtualização
  comuns — não foi testada contra todas as combinações reais de hardware/software do
  parque monitorado.
- "Usuário do console interativo" (FR-002) será obtido via `Win32_ComputerSystem.UserName`
  (ou `quser`/dono de `explorer.exe` como alternativa) — a escolha exata do método fica para
  o plano técnico, após um teste rápido contra uma máquina real (mesmo espírito de "testar
  antes de decidir" já usado nas EPICs 23/27).

## Open Questions

1. A lista de adaptadores virtuais do Data Model está boa como ponto de partida, ou você
   quer adicionar/remover algum padrão antes de aprovar a spec?
2. Para FR-002, tudo bem testar rapidamente `Win32_ComputerSystem.UserName` numa máquina
   real antes de fechar o método definitivo (mesmo padrão de validação da EPIC 27), ou você
   já tem preferência de método?

Enquanto essas duas não forem respondidas, a spec fica em **SPECIFIED**, não **APPROVED** —
sem iniciar implementação.
