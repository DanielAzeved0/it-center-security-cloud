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
* registro de Tarefa Agendada do Windows;
* desinstalacao da Tarefa Agendada.

## Objetivo

O agente deve ser instalado como componente operacional do Windows, executando check-ins periodicos contra o ambiente publicado.

No MVP, a execucao periodica usa Tarefa Agendada do Windows com usuario `SYSTEM`.

Servico Windows nativo fica reservado para evolucao futura.

## Fluxo de instalacao

```text
1. Abrir PowerShell como Administrador
2. Entrar na pasta agent-windows
3. Executar install-agent.ps1
4. Configurar URL da API
5. Configurar AGENT_API_KEY
6. Registrar Tarefa Agendada
7. Iniciar coleta periodica
8. Enviar check-ins periodicos
```

## Comando de instalacao

Ambiente publicado:

```powershell
cd agent-windows
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install-agent.ps1 `
  -ServerUrl "https://itcenter-daniel.chickenkiller.com" `
  -AgentApiKey "<AGENT_API_KEY>" `
  -CheckinIntervalMinutes 5
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
4. Criar C:\Program Files\ITCenterAgent
5. Criar logs\
6. Criar cache\
7. Copiar scripts do agente
8. Gerar config.json
9. Registrar Tarefa Agendada ITCenterAgent
```

## Configuracoes esperadas

```text
SERVER_URL=https://itcenter-daniel.chickenkiller.com
AGENT_API_KEY=<valor seguro>
CHECKIN_INTERVAL_MINUTES=5
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
  "log_path": "C:\\Program Files\\ITCenterAgent\\logs",
  "cache_path": "C:\\Program Files\\ITCenterAgent\\cache",
  "collect_inventory": true,
  "collect_metrics": true,
  "collect_security": true
}
```

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

## Requisitos pendentes

* Retry inteligente.
* Validacao contra o ambiente publicado.
* Instalador assinado.
* Atualizacao automatica.
* Servico Windows nativo.
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

## Critério de conclusão

O EPIC 8 sera considerado concluido quando:

* o agente for instalado em uma maquina Windows sem passos manuais soltos;
* o agente executar periodicamente;
* o agente enviar check-in real para producao;
* a maquina aparecer no dashboard publicado;
* logs e cache offline ficarem em locais previsiveis;
* a instalacao e a remocao estiverem documentadas.
