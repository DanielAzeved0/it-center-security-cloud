# Seguranca

Esta pasta documenta os controles de seguranca do projeto.

## Documentos

| Documento | Conteudo |
| --- | --- |
| `SECURITY.md` | Politicas e requisitos de seguranca. |
| `AUTH.md` | Autenticacao do dashboard e do agente. |
| `ASSET_POLICY.md` | Politica de ativos e softwares autorizados. |
| `SOC_RULES.md` | Regras iniciais de SOC Light. |

Documento complementar fora desta pasta: `docs/architecture/SECURITY.md` cobre segurança de infraestrutura/rede/TLS (VM, Nginx, backups, volumes); os quatro documentos acima cobrem segurança de aplicação/API/RBAC.

## Principios

* Nao versionar secrets.
* Exigir HTTPS em producao.
* Manter banco, backend e frontend sem exposicao direta.
* Autenticar usuarios humanos do dashboard com login administrativo (Bearer token HMAC SHA-256, papeis `admin`/`analyst`/`viewer` — ver `AUTH.md`); esse e o mecanismo principal, nao o Basic Auth.
* Manter o Basic Auth do Nginx apenas como camada extra de borda no MVP, redundante ao login administrativo (ver ADR-023 em `docs/development/DECISIONS.md`).
* Autenticar o agente com `X-Agent-Api-Key`.
* Registrar evolucoes de seguranca em `docs/development/DECISIONS.md`.
