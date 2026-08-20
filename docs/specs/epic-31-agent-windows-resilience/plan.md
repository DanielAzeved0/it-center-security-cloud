# Plan: EPIC 31 — Resiliência do Agente Windows

> Baseado em `spec.md` (Status: SPECIFIED). Implementação só deve começar depois que as 2
> Open Questions da spec forem respondidas e o status virar APPROVED.

## Architecture

Nenhum desvio da arquitetura existente. Todas as mudanças são internas a
`agent-windows/itcenter-agent.ps1`, seguindo o padrão já estabelecido (coletores `Get-Agent*`
com reader injetável, try/catch por função quando a fonte pode falhar de forma inesperada).

## Files to change

- `agent-windows/itcenter-agent.ps1`
  - `Get-AgentLocalAdmins` (linha ~764): envolver a chamada ao `$LocalAdminReader` em
    try/catch próprio.
  - `Get-AgentUsername` (linha ~317): adicionar tentativa de usuário do console antes do
    fallback atual.
  - `Get-AgentNetworkInfo` (linha ~343): adicionar filtro de exclusão de adaptador virtual
    antes do `Sort-Object -Property InterfaceMetric, InterfaceIndex`.
  - `Send-PendingAgentCheckins` (linha ~1182): adquirir Mutex no início, liberar em `finally`.
  - Topo do script: nova constante `$script:VirtualAdapterPatterns` (array).
- `agent-windows/tests/run-agent-tests.ps1`: novos casos para as 4 funções.
- `docs/agent/TROUBLESHOOTING.md`: documentar os 4 novos comportamentos (mesmo padrão da
  EPIC 16).
- `docs/agent/CHECKIN.md`: atualizar a descrição do campo `username` (fonte muda de
  "identidade do processo" para "usuário do console interativo, com fallback").

## Files to create

Nenhum arquivo novo no agente (mudança é toda dentro do script existente, consistente com
"sem Serviço Windows/dependência nova").

## Components

Só o agente Windows. Sem impacto em backend, banco ou frontend.

## Data changes

Nenhuma.

## API changes

Nenhuma — o schema do payload de check-in não muda (mesmos campos `local_admins`,
`username`, `ip_address`).

## Dependencies

Nenhuma dependência nova. `System.Threading.Mutex` é parte do BCL do .NET, já disponível em
qualquer PowerShell — não conta como dependência externa (ADR-005/ADR-025 continuam
satisfeitos).

## Testing Strategy

Seguir o padrão já usado em `run-agent-tests.ps1` (mock de scriptblock injetável, ex.:
"leitor que lança exceção" da EPIC 27):

- `Get-AgentLocalAdmins`: mock de `$LocalAdminReader` que lança exceção → esperar lista
  vazia + sem propagação.
- `Get-AgentLocalAdmins`: mock retornando mistura de membros válidos + um que lança exceção
  ao ler `.Name` → esperar só os válidos.
- `Get-AgentUsername`: mock do reader de usuário de console retornando um valor → esperar
  esse valor, não o do processo.
- `Get-AgentUsername`: mock do reader de console retornando vazio/null → esperar fallback
  para identidade do processo (comportamento atual).
- `Get-AgentNetworkInfo`: mock de adaptadores incluindo um "Hyper-V Virtual Ethernet
  Adapter" com métrica mais baixa que uma NIC física → esperar IP da NIC física.
- `Get-AgentNetworkInfo`: mock só com adaptador virtual → esperar fallback (IP do virtual +
  WARN), não IP nulo.
- `Send-PendingAgentCheckins`: teste de integração simulando lock já adquirido (segundo
  Mutex com mesmo nome) → esperar retorno `0` sem processar arquivos, sem exceção.

## Migration / Rollout

Nenhuma migração de dados. Rollout é substituição direta do script após reassinatura
(ADR-031) — mesmo processo de deploy do agente já usado nas EPICs 16/27. Sem necessidade de
staged rollout (EPIC 22, ainda não implementada) para uma correção de resiliência deste
tamanho.

## Risks

- Risco de FR-002 mudar o valor de `username` reportado para máquinas já em produção —
  efeito colateral esperado e desejado (é o próprio objetivo do fix), mas vale mencionar no
  changelog de deploy que o dashboard vai passar a mostrar nomes de usuário reais em vez de
  "NT AUTHORITY\SYSTEM" a partir do rollout.
- Risco de a lista de adaptadores virtuais (Data Model da spec) não cobrir um caso real do
  parque monitorado — mitigado pelo fallback explícito do FR-004 (nunca fica sem IP) e pela
  lista ser extensível.
- Timeout do Mutex mal calibrado poderia fazer uma execução legítima desistir cedo demais —
  mitigado por um teste de integração cobrindo o caminho de lock ocupado.

## Task Breakdown

```
TASK-001 (→ FR-001, AC "admin com SID órfão não derruba o check-in")
Envolver a chamada ao $LocalAdminReader em Get-AgentLocalAdmins em try/catch, logando WARN
e retornando lista vazia (ou parcial) em caso de exceção.

TASK-002 (→ FR-001)
Adicionar testes em run-agent-tests.ps1 para TASK-001 (reader que lança exceção; mistura de
membros válidos/inválidos).

TASK-003 (→ FR-002, ACs de usuário do console/fallback)
Testar rapidamente Win32_ComputerSystem.UserName (ou alternativa) contra uma máquina real
disponível, decidir o método definitivo, e implementar em Get-AgentUsername com fallback
para a identidade do processo.

TASK-004 (→ FR-002)
Adicionar testes em run-agent-tests.ps1 para TASK-003 (console user disponível; console user
indisponível → fallback).

TASK-005 (→ FR-003, ACs de execução concorrente)
Adicionar aquisição de Mutex nomeado (Local\) no início de Send-PendingAgentCheckins, com
timeout curto e liberação em finally; log INFO quando o lock estiver ocupado.

TASK-006 (→ FR-003)
Adicionar teste de integração simulando lock já adquirido.

TASK-007 (→ FR-004, ACs de seleção de IP)
Adicionar $script:VirtualAdapterPatterns e filtro de exclusão em Get-AgentNetworkInfo antes
da ordenação por métrica, com fallback + WARN quando não sobrar adaptador físico.

TASK-008 (→ FR-004)
Adicionar testes em run-agent-tests.ps1 para TASK-007 (adaptador virtual com métrica menor
que NIC física; só adaptador virtual disponível).

TASK-009
Atualizar docs/agent/TROUBLESHOOTING.md (4 novos comportamentos) e docs/agent/CHECKIN.md
(semântica do campo username).

TASK-010
Rodar run-agent-tests.ps1 completo, reassinar os scripts (Sign-AgentScripts.ps1), e
preencher verification.md antes de marcar a EPIC 31 como encerrada em TASKS.md.
```
