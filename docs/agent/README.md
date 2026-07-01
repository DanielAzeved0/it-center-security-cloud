# Agente Windows

Esta pasta documenta o agente Windows.

## Documentos

| Documento | Conteudo |
| --- | --- |
| `INSTALLATION.md` | Instalacao, desinstalacao e validacao manual do agente. |
| `CHECKIN.md` | Contrato de check-in e comunicacao com a API. |
| `TROUBLESHOOTING.md` | Diagnostico operacional de instalacao, execucao, rede, retry, cache e dashboard. |
| `README_AGENT_LEGACY.md` | Documento legado de agentes/IA preservado. |

## Estado atual

O agente PowerShell ja possui coleta local, envio para `POST /api/v1/agent/checkin`, cache offline, reenvio de check-ins pendentes, preflight de conectividade no instalador e instalacao por Tarefa Agendada do Windows.

Uma integracao do agente ja foi validada no ambiente publicado com maquina Windows real, check-in `200 OK`, persistencia no PostgreSQL, exibicao no dashboard publicado e ciclo periodico mantendo as maquinas visiveis.

A validacao evidenciada item a item do fluxo completo Windows Agent -> Nginx -> FastAPI -> PostgreSQL -> Dashboard foi registrada em `docs/development/TASKS.md` e `docs/deployment/DEPLOYMENT_HISTORY.md`.

Enquanto nenhum agente realizar check-in, o dashboard pode aparecer vazio. Depois do primeiro check-in com `200 OK`, a maquina deve aparecer no dashboard.

## Proxima fase

* Adicionar atualizacao automatica.
* Adicionar assinatura dos payloads.
