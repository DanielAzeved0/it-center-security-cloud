# Agente Windows

Esta pasta documenta o agente Windows.

## Documentos

| Documento | Conteudo |
| --- | --- |
| `INSTALLATION.md` | Instalacao, desinstalacao e validacao manual do agente. |
| `CHECKIN.md` | Contrato de check-in e comunicacao com a API. |
| `README_AGENT_LEGACY.md` | Documento legado de agentes/IA preservado. |

## Estado atual

O agente PowerShell ja possui coleta local, envio para `POST /api/v1/agent/checkin`, cache offline, reenvio de check-ins pendentes e instalacao por Tarefa Agendada do Windows.

O que ainda falta e validar o fluxo completo no ambiente publicado com uma maquina Windows real.

Enquanto nenhum agente realizar check-in, o dashboard pode aparecer vazio. Isso e esperado.

## Proxima fase

* Validar check-in real em producao.
* Confirmar maquina no dashboard publicado.
* Adicionar atualizacao automatica.
* Melhorar retry inteligente.
* Adicionar assinatura dos payloads.
