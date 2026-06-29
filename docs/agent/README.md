# Agente Windows

Esta pasta documenta o agente Windows.

## Documentos

| Documento | Conteudo |
| --- | --- |
| `INSTALLATION.md` | Instalacao, desinstalacao e validacao manual do agente. |
| `CHECKIN.md` | Contrato de check-in e comunicacao com a API. |
| `README_AGENT_LEGACY.md` | Documento legado de agentes/IA preservado. |

## Estado atual

O agente PowerShell ja possui coleta local, envio para `POST /api/v1/agent/checkin`, cache offline, reenvio de check-ins pendentes, preflight de conectividade no instalador e instalacao por Tarefa Agendada do Windows.

O fluxo completo ja foi validado no ambiente publicado com maquina Windows real.

Enquanto nenhum agente realizar check-in, o dashboard pode aparecer vazio. Depois do primeiro check-in com `200 OK`, a maquina deve aparecer no dashboard.

## Proxima fase

* Adicionar atualizacao automatica.
* Melhorar retry inteligente.
* Adicionar assinatura dos payloads.
