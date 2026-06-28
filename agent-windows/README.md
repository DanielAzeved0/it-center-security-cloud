# Agente Windows

Agente PowerShell do IT Center Security Cloud.

## Estrutura

```text
agent-windows/
  itcenter-agent.ps1
  install-agent.ps1
  uninstall-agent.ps1
  config.json
  cache/
  logs/
```

## Execucao local

```powershell
cd agent-windows
.\itcenter-agent.ps1
```

## Configuracao

`config.json` define:

```text
server_url
agent_api_key
checkin_interval_minutes
log_path
cache_path
collect_inventory
collect_metrics
collect_security
```

O valor `agent_api_key` deve ser igual ao `AGENT_API_KEY` usado pelo backend.

O agente ainda aceita os campos legados `api_key` e `interval_minutes` para compatibilidade.

`server_url` pode ser informado como raiz do ambiente publicado:

```text
https://itcenter-daniel.chickenkiller.com
```

ou como base local da API:

```text
http://127.0.0.1:8000/api/v1
```

## Instalacao no Windows

Executar em PowerShell como Administrador:

```powershell
cd agent-windows
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install-agent.ps1 `
  -ServerUrl "https://itcenter-daniel.chickenkiller.com" `
  -AgentApiKey "<AGENT_API_KEY>" `
  -CheckinIntervalMinutes 5
```

A instalacao cria:

```text
C:\Program Files\ITCenterAgent\
  itcenter-agent.ps1
  install-agent.ps1
  uninstall-agent.ps1
  config.json
  logs\
  cache\
```

E registra a Tarefa Agendada:

```text
ITCenterAgent
```

## Desinstalacao

Remover a Tarefa Agendada, preservando arquivos, logs e cache:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Program Files\ITCenterAgent\uninstall-agent.ps1"
```

Remover tambem scripts e configuracao:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Program Files\ITCenterAgent\uninstall-agent.ps1" -RemoveFiles
```

## Coletas implementadas

### Hostname

O agente coleta o hostname local usando APIs nativas do Windows/.NET.

Regra atual:

```text
1. Tenta coletar com [System.Net.Dns]::GetHostName().
2. Se vier vazio, usa a variavel de ambiente COMPUTERNAME.
3. Normaliza o valor para caixa alta.
4. Registra o hostname no log local.
```

O envio para a API sera implementado nas proximas tarefas do EPIC 4.

### Usuario

O agente coleta apenas o nome do usuario em execucao no contexto atual do processo.

Regra atual:

```text
1. Tenta coletar com [System.Security.Principal.WindowsIdentity]::GetCurrent().Name.
2. Se vier vazio, usa a variavel de ambiente USERNAME.
3. Remove espacos extras no inicio e no fim.
4. Registra o usuario no log local.
```

Esta coleta nao acessa senha, arquivos pessoais, historico, cookies ou conteudo do usuario.

### IP

O agente coleta o primeiro IPv4 ativo da maquina.

Regra atual:

```text
1. Tenta coletar com Get-NetIPAddress.
2. Ignora loopback 127.0.0.1.
3. Ignora APIPA 169.254.x.x.
4. Da preferencia para interfaces com menor metrica.
5. Se Get-NetIPAddress nao estiver disponivel, usa Win32_NetworkAdapterConfiguration via CIM.
6. Se necessario, tenta resolver o IPv4 pelo hostname local.
7. Registra o IP no log local.
8. Se nenhum IPv4 valido for encontrado, registra aviso e continua a execucao.
```

No MVP, somente IPv4 sera enviado no campo ip_address da API.

### Sistema operacional

O agente coleta o nome do sistema operacional e a versao do Windows.

Regra atual:

```text
1. Tenta ler ProductName e DisplayVersion em HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion.
2. Se faltar ProductName, usa Caption do Win32_OperatingSystem.
3. Se faltar DisplayVersion, usa ReleaseId ou Version.
4. Registra os valores no log local.
```

### Programas instalados

O agente coleta o snapshot atual dos programas instalados no Windows.

Regra atual:

```text
1. Lê as chaves de uninstall em HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall.
2. Lê também HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall.
3. Ignora entradas sem DisplayName.
4. Normaliza nome, versão e publisher.
5. Remove duplicidades por nome, versão e publisher.
6. Registra a quantidade de programas no log local.
```

Os programas instalados passam a compor o campo `installed_programs` do check-in.

### CPU

O agente coleta o uso atual de CPU em percentual.

Regra atual:

```text
1. Coleta LoadPercentage via Win32_Processor.
2. Calcula a media quando houver mais de um processador informado.
3. Normaliza o valor para ficar entre 0 e 100.
4. Registra o percentual no log local.
```

### RAM

O agente coleta o uso atual de memoria RAM em percentual.

Regra atual:

```text
1. Coleta TotalVisibleMemorySize e FreePhysicalMemory via Win32_OperatingSystem.
2. Calcula memoria usada sobre memoria total.
3. Normaliza o valor para ficar entre 0 e 100.
4. Registra o percentual no log local.
```

### Disco

O agente coleta o uso do disco principal em percentual.

Regra atual:

```text
1. Coleta discos fixos via Win32_LogicalDisk.
2. Da preferencia ao disco do sistema informado em SystemDrive.
3. Se o disco do sistema nao for encontrado, usa o primeiro disco fixo valido.
4. Calcula espaco usado sobre espaco total.
5. Normaliza o valor para ficar entre 0 e 100.
6. Registra o percentual no log local.
```

### JSON de check-in

O agente gera um JSON alinhado ao contrato atual do endpoint `POST /api/v1/agent/checkin`.

Campos gerados no momento:

```text
hostname
username
ip_address
operating_system
os_version
cpu_usage
ram_usage
disk_usage
uptime_seconds
installed_programs
security
```

Observacoes:

```text
installed_programs e preenchido com o snapshot local dos programas instalados.
security usa coletas reais de Firewall, Defender, RDP, administradores locais, USB e falhas de login.
O envio para a API ja esta implementado.
```

## Testes

Os testes do agente ficam em:

```text
agent-windows/tests/run-agent-tests.ps1
```

Execucao:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\agent-windows\tests\run-agent-tests.ps1
```

Os testes validam:

```text
Coleta de CPU entre 0 e 100
Coleta de RAM entre 0 e 100
Coleta de disco entre 0 e 100
Payload com campos obrigatorios do check-in
JSON parseavel e alinhado ao payload
Requisicao POST com header X-Agent-Api-Key
Body JSON enviado para /api/v1/agent/checkin
Normalizacao de config nova e legada
Expansao de server_url raiz para /api/v1/agent/checkin
Cache offline em arquivo JSON
Reenvio de check-ins pendentes
```

## Envio para API

O agente envia o check-in para:

```text
POST /api/v1/agent/checkin
```

Regras do envio:

```text
1. Usa server_url do config.json.
2. Anexa /api/v1 quando server_url apontar para a raiz do dominio.
3. Anexa /agent/checkin ao endpoint base.
4. Envia o header X-Agent-Api-Key.
5. Envia o payload em JSON UTF-8.
6. Se a API falhar, registra aviso e salva o payload em cache offline.
7. No proximo ciclo, tenta reenviar payloads pendentes.
```
