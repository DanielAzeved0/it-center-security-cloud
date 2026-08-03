# Troubleshooting do Agente Windows

Este guia diagnostica falhas do agente Windows instalado em:

```text
C:\Program Files\ITCenterAgent
```

Use PowerShell como Administrador para os comandos abaixo. Nunca compartilhe o valor de `agent_api_key` ou `AGENT_API_KEY`.

## 1. Agente nao aparece no dashboard

Causas provaveis:

* Tarefa Agendada ausente ou sem execucao recente.
* `config.json` apontando para URL errada.
* DNS ou porta 443 indisponivel.
* API key divergente.
* Payload preso em cache offline.
* Check-in recebido, mas dashboard ainda nao atualizado no navegador.

Diagnostico:

```powershell
Get-ScheduledTask -TaskName "ITCenterAgent"
Get-ScheduledTaskInfo -TaskName "ITCenterAgent"
Get-Content "C:\Program Files\ITCenterAgent\logs\itcenter-agent.log" -Tail 80
Get-ChildItem "C:\Program Files\ITCenterAgent\cache" -Filter "checkin-*.json"
```

Interpretacao:

* `LastTaskResult = 0`: ultima execucao terminou sem erro do agendador.
* `LastRunTime` antigo: a tarefa pode nao estar rodando no intervalo esperado.
* Arquivos `checkin-*.json`: houve falha de envio ou reenvio.
* Log com `Check-in sent successfully`: o agente conseguiu enviar para a API.

Acao corretiva:

1. Execute o agente manualmente para validar o envio.
2. Confirme DNS, porta, health check e API key.
3. Abra o dashboard em `https://itcenter-daniel.chickenkiller.com/machines`.
4. Confirme se o hostname aparece e se o ultimo check-in e recente.

Execucao manual:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Program Files\ITCenterAgent\itcenter-agent.ps1" `
  -ConfigPath "C:\Program Files\ITCenterAgent\config.json"
```

## 2. Tarefa Agendada ausente ou falhando

Diagnostico:

```powershell
Get-ScheduledTask -TaskName "ITCenterAgent"
Get-ScheduledTaskInfo -TaskName "ITCenterAgent"
```

Interpretacao:

* Erro `No MSFT_ScheduledTask objects found`: a tarefa nao existe.
* `LastTaskResult` diferente de `0`: a execucao falhou ou foi interrompida.
* `NextRunTime` vazio ou inesperado: o gatilho pode estar incorreto.

Acao corretiva:

1. Reexecute o instalador do agente com PowerShell como Administrador.
2. Confira se `C:\Program Files\ITCenterAgent\itcenter-agent.ps1` existe.
3. Rode uma execucao manual para separar erro do agente de erro do agendador.

## 3. Validar config.json

Diagnostico seguro:

```powershell
$config = Get-Content "C:\Program Files\ITCenterAgent\config.json" -Raw | ConvertFrom-Json
$config.server_url
$config.checkin_interval_minutes
$config.retry_max_attempts
$config.retry_initial_delay_seconds
$config.retry_max_delay_seconds
```

Nao imprima nem compartilhe:

```text
$config.agent_api_key
```

Valores esperados em producao:

```text
server_url=https://itcenter-daniel.chickenkiller.com
checkin_interval_minutes=5
retry_max_attempts=3
retry_initial_delay_seconds=2
retry_max_delay_seconds=15
```

Valores aceitos:

* `server_url` pode apontar para a raiz do dominio publicado.
* `server_url` local pode usar `http://127.0.0.1:8000/api/v1`.
* Configs legadas com `api_key` e `interval_minutes` continuam aceitas.
* `log_max_size_kb` (padrao 5120), `log_max_backups` (padrao 3) e `cache_retention_days` (padrao 30) sao opcionais; se omitidos, o agente usa esses defaults.

Desde o hardening da EPIC 16, o instalador restringe a ACL de `config.json` a `SYSTEM`/`Administrators`. Se precisar ler o arquivo manualmente e receber "Acesso negado", execute o PowerShell como Administrador:

```powershell
Get-Acl "C:\Program Files\ITCenterAgent\config.json" | Format-List
```

## 4. DNS e porta 443

Diagnostico:

```powershell
nslookup itcenter-daniel.chickenkiller.com
nslookup itcenter-daniel.chickenkiller.com 1.1.1.1
nslookup itcenter-daniel.chickenkiller.com 8.8.8.8
Test-NetConnection itcenter-daniel.chickenkiller.com -Port 443
```

Interpretacao:

* DNS sem resposta: o provedor ou rede local nao resolve o dominio.
* `TcpTestSucceeded: False`: porta 443 bloqueada ou destino indisponivel.
* DNS publico resolve, mas DNS padrao nao resolve: problema de DNS local.

Acao corretiva:

1. Ajuste DNS da rede ou da maquina para resolvers confiaveis.
2. Libere saida TCP 443 no firewall local/rede.
3. Evite usar `hosts` como solucao permanente.

## 5. Health check

Producao com URL raiz:

```powershell
Invoke-WebRequest -Uri "https://itcenter-daniel.chickenkiller.com/healthz" -UseBasicParsing
```

API local:

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/health" -UseBasicParsing
```

Interpretacao:

* HTTP `200`: endpoint esta acessivel.
* Timeout ou erro de conexao: tratar como falha temporaria de rede/infra.
* HTTP `5xx`: tratar como falha temporaria do servidor.

## 6. HTTP 401 ou 403

Causa provavel:

* `agent_api_key` do `config.json` nao corresponde ao `AGENT_API_KEY` configurado na producao.

Diagnostico:

```powershell
Get-Content "C:\Program Files\ITCenterAgent\logs\itcenter-agent.log" -Tail 80
```

Interpretacao:

* `HTTP 401` ou `HTTP 403`: falha permanente de autenticacao/autorizacao.
* O agente nao deve insistir com retry excessivo nesses codigos.

Acao corretiva:

1. Compare a origem da API key sem registrar o valor em logs ou prints publicos.
2. Reinstale ou atualize o agente com a API key correta.
3. Execute o agente manualmente e confirme `Check-in sent successfully`.

## 7. HTTP 400 ou 422

Causa provavel:

* Payload invalido ou contrato divergente.

Diagnostico:

```powershell
Get-Content "C:\Program Files\ITCenterAgent\logs\itcenter-agent.log" -Tail 120
```

Interpretacao:

* `HTTP 400` ou `HTTP 422`: falha permanente de payload.
* Retry excessivo nao e esperado.

Acao corretiva:

1. Verifique se o agente instalado esta atualizado.
2. Rode os testes locais do agente no repositorio de desenvolvimento.
3. Escale para backend/agente se o payload atual estiver incompatível com a API.

## 8. HTTP 5xx, timeout ou falha de rede

Causa provavel:

* Falha temporaria da API, Nginx, rede, DNS ou rota.

Comportamento esperado:

* O agente aplica retry com atraso progressivo.
* Se as tentativas esgotarem, salva o payload em cache offline.
* No proximo ciclo, tenta reenviar payloads pendentes antes do check-in atual.

Diagnostico:

```powershell
Get-Content "C:\Program Files\ITCenterAgent\logs\itcenter-agent.log" -Tail 120
Get-ChildItem "C:\Program Files\ITCenterAgent\cache" -Filter "checkin-*.json"
```

Interpretacao:

* Logs com `temporary`, `HTTP 5xx`, `timeout` ou `Retry limit reached`: falha temporaria esgotou tentativas.
* Arquivos no cache indicam payloads aguardando reenvio.

Acao corretiva:

1. Valide DNS, porta 443 e health check.
2. Aguarde o proximo ciclo automatico.
3. Ou force execucao manual para testar o reenvio.

## 9. Cache offline com arquivos pendentes

Diagnostico:

```powershell
Get-ChildItem "C:\Program Files\ITCenterAgent\cache" -Filter "checkin-*.json" |
  Select-Object Name, Length, LastWriteTime
```

Interpretacao:

* Poucos arquivos recentes: falha temporaria recente.
* Muitos arquivos acumulados: agente nao consegue entregar check-ins ha varios ciclos.

Acao corretiva:

1. Nao apague o cache como primeira medida.
2. Corrija conectividade ou autenticacao.
3. Execute o agente manualmente para tentar reenviar.
4. Confirme se os arquivos diminuem apos envio bem-sucedido.

Desde a EPIC 16:

* Um arquivo de cache corrompido (JSON invalido) e movido automaticamente para `cache\quarantine\` e nao bloqueia mais o reenvio dos arquivos mais novos. Investigue o conteudo do arquivo em quarentena antes de descarta-lo.
* Arquivos com mais de `cache_retention_days` (padrao 30 dias), incluindo os que estao em `cache\quarantine\`, sao removidos automaticamente a cada ciclo.

```powershell
Get-ChildItem "C:\Program Files\ITCenterAgent\cache\quarantine" -File -ErrorAction SilentlyContinue
```

## 10. Logs ausentes ou vazios

Diagnostico:

```powershell
Test-Path "C:\Program Files\ITCenterAgent\logs"
Get-ChildItem "C:\Program Files\ITCenterAgent\logs"
```

Causas provaveis:

* Agente nunca executou.
* Tarefa Agendada nao foi criada.
* Permissao de escrita no diretorio de logs.
* Caminho `log_path` divergente no `config.json`.

Acao corretiva:

1. Execute manualmente o agente como Administrador.
2. Confirme `log_path` no `config.json`.
3. Reinstale o agente se a estrutura estiver incompleta.

Desde a EPIC 16, o log e rotacionado por tamanho: ao atingir `log_max_size_kb` (padrao 5120 KB), `itcenter-agent.log` vira `itcenter-agent.log.1` e os backups anteriores deslocam até `log_max_backups` (padrao 3) antes de serem descartados. Se `itcenter-agent.log` estiver vazio mas pequeno, verifique os arquivos `.1`, `.2`, etc. no mesmo diretorio.

Uma falha de configuracao/inicializacao (ex.: `config.json` invalido) agora e registrada com `[ERROR]` no log antes do agente encerrar com erro:

```powershell
Select-String -Path "C:\Program Files\ITCenterAgent\logs\itcenter-agent.log*" -Pattern "\[ERROR\]"
```

## 11. Validacao final no dashboard

Depois de corrigir a causa:

```text
1. Acessar https://itcenter-daniel.chickenkiller.com/machines
2. Autenticar com Basic Auth
3. Confirmar hostname da maquina
4. Confirmar ultimo check-in recente
5. Confirmar que nao ha crescimento continuo de cache offline
```

Se o log mostra sucesso, mas o dashboard segue vazio:

1. Recarregue a tela.
2. Confirme se esta na tela `/machines`.
3. Verifique se o backend lista a maquina.
4. Escale para dashboard/backend se API e banco estiverem corretos.

## 12. Quando escalar

Escalar para backend/infra quando:

* Health check de producao falhar.
* Containers estiverem unhealthy.
* HTTP `5xx` persistir por varios ciclos.
* Log indicar payload valido enviado com sucesso, mas dashboard/API nao exibirem dados.

Escalar para agente quando:

* HTTP `400` ou `422` ocorrer com agente atualizado.
* O agente nao gerar payload.
* Logs mostrarem erro de coleta local.
* A Tarefa Agendada executa, mas o script falha antes do envio.
