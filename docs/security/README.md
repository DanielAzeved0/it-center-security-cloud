# Seguranca

Esta pasta documenta os controles de seguranca do projeto.

## Documentos

| Documento | Conteudo |
| --- | --- |
| `SECURITY.md` | Politicas e requisitos de seguranca. |
| `AUTH.md` | Autenticacao do dashboard e do agente. |
| `ASSET_POLICY.md` | Politica de ativos e softwares autorizados. |
| `SOC_RULES.md` | Regras iniciais de SOC Light. |

## Principios

* Nao versionar secrets.
* Exigir HTTPS em producao.
* Manter banco, backend e frontend sem exposicao direta.
* Autenticar o dashboard com Basic Auth no MVP.
* Autenticar o agente com `X-Agent-Api-Key`.
* Registrar evolucoes de seguranca em `docs/development/DECISIONS.md`.
