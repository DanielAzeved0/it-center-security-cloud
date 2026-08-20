# Research: EPIC 31 — Resiliência do Agente Windows

## Arquitetura existente relevante

`agent-windows/itcenter-agent.ps1` segue um padrão consistente: cada coletor `Get-Agent*`
aceita um parâmetro `[scriptblock]` injetável (ex.: `$LocalAdminReader`, `$UsbDeviceReader`,
`$BiosReader`) para permitir mock em teste sem depender do ambiente real. `New-AgentCheckinPayload`
(linha 893) monta o payload chamando os coletores em sequência; `Start-ItCenterAgent` (linha
1239) envolve a construção do payload num único `try/catch` de nível superior (EPIC 16) que
**loga e relança (`throw`)** qualquer exceção — ou seja, uma exceção não tratada em qualquer
coletor termina o script antes de chegar ao código que salvaria o payload em cache offline.

## Os 4 achados, confirmados linha a linha (numeração atual, já mudou um pouco desde a
auditoria de 2026-08-15 por edições posteriores)

1. **`Get-AgentLocalAdmins` (linha 764), chamada por `Get-AgentSecurityPayload` (linha 887),
   sem try/catch próprio.** `Get-LocalGroupMember` (linha 774) é chamado com
   `-ErrorAction SilentlyContinue`, mas essa é uma exceção conhecida no PowerShell: quando um
   membro do grupo tem um SID que não resolve para nome (conta de domínio removida, SID
   órfão), o cmdlet lança um erro **terminante** que ignora `-ErrorAction`. Comparando com os
   demais coletores: `Get-AgentFirewallEnabled`/`Get-AgentDefenderEnabled`/`Get-AgentRdpEnabled`
   não têm try/catch próprio, mas os cmdlets que usam (`Get-NetFirewallProfile`,
   `Get-MpComputerStatus`, `Get-ItemProperty`) respeitam `-ErrorAction` de verdade — não é o
   mesmo caso. `Get-AgentSerialNumber` (linha 438) e `Get-AgentFailedLoginsLastHour` (linha
   862) já têm try/catch próprio exatamente por lidarem com fontes que podem falhar de forma
   inesperada — `Get-AgentLocalAdmins` é a exceção que ficou sem essa proteção.

2. **`Get-AgentUsername` (linha 317) sempre reporta o usuário do processo.** Usa
   `[System.Security.Principal.WindowsIdentity]::GetCurrent().Name`. A Tarefa Agendada é
   registrada em `install-agent.ps1:274` com
   `New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest` — ou seja, em produção,
   todo check-in roda como `NT AUTHORITY\SYSTEM`, nunca o usuário logado interativamente.
   Mudar o principal da tarefa está fora de escopo (quebraria o modelo de privilégio já
   validado nas EPICs 8/16, e o updater da EPIC 22 herdaria o mesmo principal); a correção
   tem que ser dentro do próprio coletor.

3. **`Send-PendingAgentCheckins` (linha 1182) sem lock.** O `-MultipleInstances IgnoreNew`
   da Tarefa Agendada só impede duas instâncias *agendadas* simultâneas — não impede uma
   execução manual (já documentada como ação válida em `docs/agent/TROUBLESHOOTING.md`)
   enquanto o ciclo agendado roda. Dois processos podem iterar o mesmo diretório de cache;
   quem perde a corrida do `Remove-Item -LiteralPath $pendingFile.FullName` (linha 1227) cai
   no `catch` (linha 1230) que já faz `break` — abandonando o resto da fila até o próximo
   ciclo. Não existe hoje nenhum uso de `Mutex`/lock no arquivo (grep confirmado).

4. **`Get-AgentNetworkInfo` (linha 343) não exclui adaptadores virtuais/VPN.** A ordenação é
   só por `InterfaceMetric, InterfaceIndex` (linha 354). Ferramentas VPN já rastreadas em
   `docs/security/ASSET_POLICY.md` (Hamachi, ZeroTier, Radmin, Tailscale) e adaptadores
   comuns de virtualização (Hyper-V `vEthernet`, WSL, Docker Desktop, VirtualBox Host-Only)
   costumam expor métrica mais baixa que a NIC física, sem nenhum aviso no log.

## Convenções a seguir

- Toda função nova/alterada de coleta segue o padrão `Get-Agent*` com parâmetro de reader
  injetável quando fizer sentido para teste (mesmo padrão do EPIC 27 para
  `Get-AgentSerialNumber`).
- Sem dependências externas (ADR-005/ADR-025): qualquer mecanismo de lock deve usar BCL do
  .NET já disponível no PowerShell (`System.Threading.Mutex`), nunca módulo de terceiro.
- Funções de cache já existentes a reaproveitar: `Get-AgentCacheDirectory`,
  `Remove-AgentExpiredCacheFiles`, `Move-AgentCacheFileToQuarantine` (todas da EPIC 16).
- Scripts do agente são assinados (ADR-031); qualquer edição exige re-assinatura antes de
  deploy real (`Sign-AgentScripts.ps1`), já documentado em `docs/agent/TROUBLESHOOTING.md`.

## Testes existentes relacionados

`agent-windows/tests/run-agent-tests.ps1` é o único runner; testa coletores substituindo o
scriptblock injetável por um mock (ex.: EPIC 27 testou `Get-AgentSerialNumber` com "leitor
que lança exceção"). O fix de `Get-AgentLocalAdmins` deve seguir o mesmo padrão de teste:
mock de `$LocalAdminReader` que lança exceção, e confirmar que a função retorna lista vazia
em vez de propagar.

## Decisões arquiteturais relevantes

- ADR-025: gaps de robustez do agente são gaps de implementação, não da linguagem — reforça
  que estes 4 itens devem ser corrigidos em PowerShell mesmo, sem reabrir a discussão de
  reescrita.
- ADR-031: certificado de assinatura de código já existe; nenhuma mudança necessária aqui,
  só reassinar após editar.

## Perguntas em aberto levadas para Requirements Discovery

- Lista exata de descrições de adaptador virtual/VPN a excluir da seleção de IP (item 4) —
  não há uma lista "canônica" no projeto hoje; precisa ser definida e documentada como
  extensível, não hardcoded para sempre.
- Item 2 (usuário do console): qual fonte usar quando não houver sessão interativa (ex.:
  servidor sem ninguém logado) — precisa de fallback explícito, não pode virar `null`/exceção
  silenciosa.
