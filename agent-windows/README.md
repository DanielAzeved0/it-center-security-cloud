# Agente Windows

Agente PowerShell do IT Center Security Cloud.

## Estrutura

```text
agent-windows/
  itcenter-agent.ps1
  itcenter-agent-updater.ps1
  install-agent.ps1
  uninstall-agent.ps1
  itcenter-agent-signing.cer
  config.json
  update-state.json
  scripts/
    New-AgentSigningCertificate.ps1
    Sign-AgentScripts.ps1
  tests/
    run-agent-tests.ps1
    run-install-agent-tests.ps1
    run-agent-updater-tests.ps1
  cache/
  logs/
```

`itcenter-agent-updater.ps1` e `update-state.json` sao da EPIC 22 (ADR-032, auto-atualizacao) — o updater roda numa Tarefa Agendada propria (`ITCenterAgentUpdater`), separada da de coleta, e loga em `logs\itcenter-agent-updater.log` (arquivo distinto de `itcenter-agent.log`). Detalhes em `docs/agent/CHECKIN.md` (secao "EPIC 22").

## Execucao local

```powershell
cd agent-windows
.\itcenter-agent.ps1
```

O agente le `config.json` (ou o caminho passado em `-ConfigPath`) para obter `server_url`, `agent_api_key` e demais parametros de execucao. O schema completo de `config.json`, o fluxo de instalacao/desinstalacao e o code-signing (ADR-031) estao documentados em `docs/agent/INSTALLATION.md`.

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
Defaults de retry inteligente
Expansao de server_url raiz para /api/v1/agent/checkin
Cache offline em arquivo JSON
Reenvio de check-ins pendentes
Retry em falhas temporarias sem expor API key em logs
Envio de agent_version no payload de check-in (EPIC 22)
Atualizacao do contador de sucesso/falha em update-state.json (EPIC 22)
```

O instalador tem um teste separado:

```text
agent-windows/tests/run-install-agent-tests.ps1
```

Ele valida a funcao `Get-AgentScheduledTaskExecutionPolicy` (fallback `AllSigned`/`Bypass` do ADR-031) e, desde a EPIC 22, tambem o registro da Tarefa Agendada `ITCenterAgentUpdater` (validacao de assinatura do updater, execution policy correta no segundo `New-ScheduledTaskAction`) — nao cobre o preflight de conectividade (DNS/TCP/health check) do instalador, que hoje nao tem teste automatizado.

O updater dedicado (EPIC 22) tem seu proprio teste:

```text
agent-windows/tests/run-agent-updater-tests.ps1
```

Cobre: leitura de `$script:AgentVersion` instalado, validacao de assinatura/hash sem fallback, atualizacao valida (backup + substituicao atomica), hold-back por `target_agent_version`, rollback apos falhas consecutivas, confirmacao apos sucessos consecutivos, e no-op em maquinas sem `update-state.json`.

## Documentacao complementar

Este README cobre apenas a pasta de codigo (estrutura de arquivos, execucao local e testes). Para o restante:

* Instalacao, desinstalacao, schema de `config.json` e code-signing (ADR-031): `docs/agent/INSTALLATION.md`.
* Contrato de dados do check-in (campos coletados, regras de coleta, envio para a API, efeitos SOC): `docs/agent/CHECKIN.md`.
* Diagnostico operacional: `docs/agent/TROUBLESHOOTING.md`.
