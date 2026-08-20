# Instalacao do agente

Este documento registra o plano de instalacao do agente Windows.

## Estado atual

O agente ja possui scripts de instalacao e desinstalacao para Windows.

Ja existem:

* coleta local;
* geracao de JSON;
* envio para `POST /api/v1/agent/checkin`;
* header `X-Agent-Api-Key`;
* cache offline;
* reenvio de check-ins pendentes;
* logs locais do agente.
* instalacao em `C:\Program Files\ITCenterAgent`;
* registro de Tarefa Agendada do Windows (coleta - `ITCenterAgent` - e updater - `ITCenterAgentUpdater`, EPIC 22);
* desinstalacao das 2 Tarefas Agendadas.
* validacao previa de DNS, porta TCP e health check do endpoint antes da instalacao.
* auto-atualizacao do agente de coleta via updater dedicado (EPIC 22, ADR-032) - ver `docs/agent/CHECKIN.md`.

## Objetivo

O agente deve ser instalado como componente operacional do Windows, executando check-ins periodicos contra o ambiente publicado.

No MVP, a execucao periodica usa Tarefa Agendada do Windows com usuario `SYSTEM`.

Servico Windows nativo fica reservado para evolucao futura.

## Requisitos

* Windows 10 ou Windows 11.
* **Windows PowerShell 5.1** (o `powershell.exe` nativo do Windows) — o agente nao foi testado nem e suportado em PowerShell 7/`pwsh`. O script usa cmdlets exclusivos do Windows PowerShell (`Get-LocalGroupMember`, `Get-AppxPackage -AllUsers`, `Get-Counter`) que nao tem garantia de disponibilidade no PowerShell 7.
* Privilegios de Administrador para rodar `install-agent.ps1` (a Tarefa Agendada resultante roda como `SYSTEM`).
* Conectividade de rede com o endpoint da API (ver "Preflight de rede do instalador" abaixo).

## Fluxo de instalacao

```text
1. Abrir PowerShell como Administrador
2. Entrar na pasta agent-windows
3. Executar install-agent.ps1
4. Configurar URL da API
5. Configurar AGENT_API_KEY
6. Validar DNS, porta e health check do servidor
7. Registrar Tarefa Agendada
8. Iniciar coleta periodica
9. Enviar check-ins periodicos
```

## Comando de instalacao

**Atencao (ADR-031):** ao instalar a partir de um clone/checkout do repositorio-fonte (e nao de um pacote de release ja assinado), o certificado `agent-windows\itcenter-agent-signing.cer` normalmente ainda nao existe — ele so e gerado pelo mantenedor, uma unica vez, numa maquina de confianca (nunca numa maquina monitorada). Sem ele, o comando abaixo falha em "Signing certificate not found" antes de copiar qualquer arquivo. Antes de rodar o comando padrao:

```text
1. Gerar o certificado uma unica vez com agent-windows\scripts\New-AgentSigningCertificate.ps1.
2. Assinar os 4 scripts com agent-windows\scripts\Sign-AgentScripts.ps1 (inclui itcenter-agent-updater.ps1, EPIC 22).
```

Ou, para instalacao local/dev sem assinatura, adicione `-SkipSignatureCheck` ao comando (a Tarefa Agendada volta a usar `ExecutionPolicy Bypass` nesse caso — nunca use isso em producao). Detalhes completos na secao "Code-signing do agente (ADR-031)" mais abaixo.

Ambiente publicado:

```powershell
cd agent-windows
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install-agent.ps1 `
  -ServerUrl "https://itcenter-daniel.chickenkiller.com" `
  -AgentApiKey "<AGENT_API_KEY>" `
  -CheckinIntervalMinutes 5 `
  -Force
```

Ambiente local:

```powershell
cd agent-windows
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install-agent.ps1 `
  -ServerUrl "http://127.0.0.1:8000/api/v1" `
  -AgentApiKey "change-me" `
  -CheckinIntervalMinutes 5 `
  -Force
```

## Fluxo interno da instalacao

```text
1. Validar execucao como Administrador
2. Configurar URL da API
3. Configurar AGENT_API_KEY
4. Resolver DNS do host configurado
5. Validar conexao TCP na porta do endpoint
6. Validar health check do endpoint
7. Importar certificado de assinatura em LocalMachine\Root e LocalMachine\TrustedPublisher (ADR-031)
8. Validar assinatura Authenticode dos scripts de origem, agora que a cadeia e confiavel (ADR-031), incluindo itcenter-agent-updater.ps1 (EPIC 22)
9. Criar C:\Program Files\ITCenterAgent
10. Criar logs\
11. Criar cache\
12. Copiar scripts do agente, incluindo itcenter-agent-updater.ps1 (EPIC 22)
13. Gerar config.json (inclui updater_interval_hours, EPIC 22)
14. Restringir ACL de config.json a SYSTEM/Administrators (EPIC 16)
15. Registrar Tarefa Agendada ITCenterAgent com ExecutionPolicy AllSigned
16. Registrar Tarefa Agendada ITCenterAgentUpdater, mesmo principal/ExecutionPolicy, frequencia padrao 24h (EPIC 22, ADR-032)
```

O certificado precisa ser importado antes da validacao de assinatura: numa maquina nova, a cadeia de confianca ainda nao existe, e `Get-AuthenticodeSignature` reportaria `NotTrusted` mesmo para um script legitimamente assinado se o certificado so fosse importado depois.

## Preflight de rede do instalador

Por padrao, o instalador bloqueia a instalacao se o endpoint do agente nao estiver acessivel. Isso evita instalar o agente em maquinas cujo DNS local nao resolve o dominio de producao, o que faria os check-ins acumularem em cache.

Validacoes feitas antes de copiar arquivos:

```text
1. DNS do host informado em ServerUrl.
2. Conexao TCP na porta 443 para HTTPS ou 80 para HTTP local.
3. Health check:
   - ServerUrl raiz: /healthz
   - ServerUrl terminado em /api/v1: /api/v1/health
```

Se a rede usar DNS de provedor que nao resolve o dominio publicado, corrija o DNS da rede antes de instalar. Preferencias recomendadas:

```text
DNS primario: 1.1.1.1
DNS secundario: 8.8.8.8
```

Para validar manualmente no Windows:

```powershell
nslookup itcenter-daniel.chickenkiller.com
nslookup itcenter-daniel.chickenkiller.com 1.1.1.1
Test-NetConnection itcenter-daniel.chickenkiller.com -Port 443
```

Bypass operacional, apenas quando a instalacao offline for intencional:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install-agent.ps1 `
  -ServerUrl "https://itcenter-daniel.chickenkiller.com" `
  -AgentApiKey "<AGENT_API_KEY>" `
  -CheckinIntervalMinutes 5 `
  -SkipConnectivityCheck `
  -Force
```

Nao use `hosts` como solucao padrao para distribuir agentes. Se o IP publico mudar, cada maquina ficara presa ao IP antigo.

## Code-signing do agente (ADR-031)

Desde a resolucao do ultimo item pendente da EPIC 16, a Tarefa Agendada roda com `ExecutionPolicy AllSigned` em vez de `Bypass`: qualquer script (`itcenter-agent.ps1`, `install-agent.ps1`, `uninstall-agent.ps1`) precisa ter uma assinatura Authenticode valida para ser executado. Isso fecha o vetor em que um script sobrescrito localmente no disco seria executado como `SYSTEM` sem nenhuma verificacao.

Certificado usado: Authenticode **self-signed** (gratuito, sem CA publica), gerado uma unica vez com `agent-windows\scripts\New-AgentSigningCertificate.ps1` numa maquina de confianca do mantenedor (nunca numa maquina monitorada), com validade de 10 anos. A chave privada (`.pfx`) nunca e versionada nem usada em CI. So a chave publica (`itcenter-agent-signing.cer`) e distribuida, embutida no pacote de instalacao.

Fluxo de release do agente (obrigatorio antes de distribuir qualquer atualizacao dos scripts):

```text
1. Editar os scripts do agente normalmente.
2. Rodar agent-windows\scripts\Sign-AgentScripts.ps1 com o .pfx do mantenedor -
   isso deve ser o ultimo passo antes de empacotar, pois qualquer edicao
   posterior invalida a assinatura.
3. Confirmar que agent-windows\itcenter-agent-signing.cer corresponde ao
   certificado usado (so precisa trocar se o certificado for regenerado).
4. Distribuir/instalar a partir dos scripts ja assinados.
```

O instalador valida a assinatura dos 4 scripts de origem (`Get-AuthenticodeSignature` com `Status -eq 'Valid'`, incluindo itcenter-agent-updater.ps1 desde a EPIC 22) antes de copiar qualquer arquivo, e falha cedo com mensagem clara se algum nao estiver assinado.

Bypass consciente, apenas para instalacao local/dev sem certificado configurado (a Tarefa Agendada volta a usar `Bypass` nesse caso — nunca use isso em producao):

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install-agent.ps1 `
  -ServerUrl "http://127.0.0.1:8000/api/v1" `
  -AgentApiKey "change-me" `
  -CheckinIntervalMinutes 5 `
  -SkipSignatureCheck `
  -Force
```

## Configuracoes esperadas

Nao sao variaveis de ambiente — sao parametros do instalador (`-ServerUrl`, `-AgentApiKey`, `-CheckinIntervalMinutes`), passados na linha de comando e persistidos por `install-agent.ps1` em `config.json` com chaves em snake_case:

```text
-ServerUrl "https://itcenter-daniel.chickenkiller.com"
-AgentApiKey "<valor seguro>"
-CheckinIntervalMinutes 5
```

Arquivo gerado:

```text
C:\Program Files\ITCenterAgent\config.json
```

Schema:

```json
{
  "server_url": "https://itcenter-daniel.chickenkiller.com",
  "agent_api_key": "<valor seguro>",
  "checkin_interval_minutes": 5,
  "retry_max_attempts": 3,
  "retry_initial_delay_seconds": 2,
  "retry_max_delay_seconds": 15,
  "log_path": "C:\\Program Files\\ITCenterAgent\\logs",
  "cache_path": "C:\\Program Files\\ITCenterAgent\\cache",
  "log_max_size_kb": 5120,
  "log_max_backups": 3,
  "cache_retention_days": 30,
  "collect_inventory": true,
  "collect_metrics": true,
  "collect_security": true
}
```

Desde a EPIC 16, o instalador restringe a ACL deste arquivo a `SYSTEM`/`Administrators`, protegendo o `agent_api_key` em texto puro contra leitura por usuarios comuns.

## Comando de desinstalacao

Remover apenas a execucao periodica, preservando arquivos, logs e cache:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Program Files\ITCenterAgent\uninstall-agent.ps1"
```

Remover scripts e configuracao, preservando logs e cache:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Program Files\ITCenterAgent\uninstall-agent.ps1" -RemoveFiles
```

Remover tambem logs e cache:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Program Files\ITCenterAgent\uninstall-agent.ps1" -RemoveFiles -RemoveData
```

## Requisitos implementados

* Script de instalacao.
* Script de desinstalacao.
* Tarefa Agendada controlada.
* Configuracao persistente de `SERVER_URL`.
* Configuracao persistente de `AGENT_API_KEY`.
* Local padrao de logs.
* Local padrao de cache offline.
* Preflight de conectividade antes da instalacao.
* Retry inteligente para falhas temporarias.
* ACL de `config.json` restrita a SYSTEM/Administrators (EPIC 16).
* Quarentena de cache corrompido e retencao por idade em `cache\` (EPIC 16).
* Rotacao de `logs\itcenter-agent.log` por tamanho (EPIC 16).
* Instalador/scripts assinados (code-signing) com certificado Authenticode self-signed e Tarefa Agendada com `ExecutionPolicy AllSigned` (EPIC 16, ADR-031).

## Requisitos pendentes

* Atualizacao automatica — plano formal registrado em ADR-032/EPIC 22 (`docs/development/DECISIONS.md`, `docs/development/TASKS.md`); implementacao ainda pendente.
* Servico Windows nativo — resolvido parcialmente para atualizacao automatica via Tarefa Agendada dedicada (ADR-032/EPIC 22); o caso geral (servico Windows via SCM para a coleta em si) continua pendente.
* Criptografia e assinatura de payloads.

## Estrutura esperada no Windows

```text
C:\Program Files\ITCenterAgent\
|-- itcenter-agent.ps1
|-- config.json
|-- install-agent.ps1
|-- uninstall-agent.ps1
|-- logs\
`-- cache\
    `-- quarantine\
```

## Validacoes manuais esperadas

Executar instalacao em Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\agent-windows\install-agent.ps1 `
  -ServerUrl "https://itcenter-daniel.chickenkiller.com" `
  -AgentApiKey "<AGENT_API_KEY>" `
  -CheckinIntervalMinutes 5 `
  -Force
```

Confirmar diretorio:

```powershell
Test-Path "C:\Program Files\ITCenterAgent"
Get-ChildItem "C:\Program Files\ITCenterAgent"
```

Confirmar Tarefa Agendada:

```powershell
Get-ScheduledTask -TaskName "ITCenterAgent"
```

Confirmar ExecutionPolicy `AllSigned` na acao da Tarefa Agendada (ADR-031):

```powershell
(Get-ScheduledTask -TaskName "ITCenterAgent").Actions.Arguments
```

Confirmar certificado de assinatura importado:

```powershell
Get-ChildItem Cert:\LocalMachine\Root, Cert:\LocalMachine\TrustedPublisher |
  Where-Object { $_.Subject -eq "CN=IT Center Security Cloud Agent" }
```

Executar check-in manual:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Program Files\ITCenterAgent\itcenter-agent.ps1" `
  -ConfigPath "C:\Program Files\ITCenterAgent\config.json"
```

Confirmar log local:

```powershell
Get-Content "C:\Program Files\ITCenterAgent\logs\itcenter-agent.log" -Tail 50
```

Confirmar cache offline simulando API indisponivel:

```powershell
$configPath = "C:\Program Files\ITCenterAgent\config.json"
$config = Get-Content $configPath -Raw | ConvertFrom-Json
$originalUrl = $config.server_url
$config.server_url = "https://127.0.0.1:9"
$config | ConvertTo-Json -Depth 5 | Set-Content $configPath -Encoding UTF8

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Program Files\ITCenterAgent\itcenter-agent.ps1" `
  -ConfigPath $configPath

Get-ChildItem "C:\Program Files\ITCenterAgent\cache" -Filter "checkin-*.json"
```

Confirmar reenvio apos API disponivel:

```powershell
$config = Get-Content $configPath -Raw | ConvertFrom-Json
$config.server_url = $originalUrl
$config | ConvertTo-Json -Depth 5 | Set-Content $configPath -Encoding UTF8

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Program Files\ITCenterAgent\itcenter-agent.ps1" `
  -ConfigPath $configPath

Get-ChildItem "C:\Program Files\ITCenterAgent\cache" -Filter "checkin-*.json"
```

Confirmar maquina no dashboard publicado:

```text
1. Acessar https://itcenter-daniel.chickenkiller.com
2. Autenticar com Basic Auth
3. Abrir a tela de maquinas
4. Confirmar hostname da maquina Windows
5. Confirmar ultimo check-in recente
```

## Estado de validacao

Validado:

* o agente foi instalado em uma maquina Windows sem passos manuais soltos;
* o agente executa periodicamente e mantem a maquina visivel no dashboard;
* o agente envia check-in real para producao;
* a maquina aparece no dashboard publicado;
* logs e cache offline ficam em locais previsiveis;
* a instalacao e a remocao estao documentadas.

Documentacao complementar:

* troubleshooting operacional do agente em `docs/agent/TROUBLESHOOTING.md`.
