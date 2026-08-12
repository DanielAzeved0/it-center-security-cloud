# Agente Windows

Esta pasta documenta o agente Windows.

## Documentos

| Documento | Conteudo |
| --- | --- |
| `INSTALLATION.md` | Instalacao, desinstalacao e validacao manual do agente. |
| `CHECKIN.md` | Contrato de check-in e comunicacao com a API. |
| `TROUBLESHOOTING.md` | Diagnostico operacional de instalacao, execucao, rede, retry, cache e dashboard. |
| `agent-windows/README.md` | README tecnico da pasta de codigo: estrutura de arquivos, execucao local e testes. |

O documento legado de orquestracao de agentes de IA (anterior ao `CLAUDE.md` e aos subagents nativos) foi movido para `docs/development/README_AGENT_LEGACY.md` — nao e sobre o agente Windows, entao nao faz mais parte do indice desta pasta.

## Estado atual

O agente PowerShell ja possui coleta local, envio para `POST /api/v1/agent/checkin`, cache offline, reenvio de check-ins pendentes, preflight de conectividade no instalador e instalacao por Tarefa Agendada do Windows.

A EPIC 16 (hardening do agente) esta concluida: ACL restrita em `config.json` (leitura so SYSTEM/Administrators), quarentena de cache corrompido, retencao por idade em `cache/`, rotacao de `logs/` por tamanho, medicao de CPU via `Get-Counter` amostrado, inventario incluindo apps UWP/Store (`Get-AppxPackage`), deteccao de USB ampliada (`Win32_PnPEntity`) e try/catch de alto nivel em `Start-ItCenterAgent`. O ultimo item pendente da EPIC 16, assinatura de codigo, foi resolvido com certificado Authenticode self-signed e Tarefa Agendada com `ExecutionPolicy AllSigned` (ADR-031). Detalhes completos em `docs/agent/INSTALLATION.md` e `docs/agent/CHECKIN.md`.

Uma integracao do agente ja foi validada no ambiente publicado com maquina Windows real, check-in `200 OK`, persistencia no PostgreSQL, exibicao no dashboard publicado e ciclo periodico mantendo as maquinas visiveis.

A validacao evidenciada item a item do fluxo completo Windows Agent -> Nginx -> FastAPI -> PostgreSQL -> Dashboard foi registrada em `docs/development/TASKS.md` e `docs/deployment/DEPLOYMENT_HISTORY.md`.

Enquanto nenhum agente realizar check-in, o dashboard pode aparecer vazio. Depois do primeiro check-in com `200 OK`, a maquina deve aparecer no dashboard.

## Proxima fase

* Atualizacao automatica: planejamento completo em ADR-032/EPIC 22 (2026-08-10, `docs/development/DECISIONS.md`, `docs/development/TASKS.md`), implementacao ainda pendente.
* Auto-deteccao do ID do RustDesk pelo agente, sem substituir o cadastro manual: planejamento completo em ADR-034/EPIC 23, implementacao ainda pendente.
* Adicionar assinatura dos payloads (sem plano formal ainda).
