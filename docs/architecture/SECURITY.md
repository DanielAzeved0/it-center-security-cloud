# Security Architecture

Este documento resume os controles de seguranca aplicados na **infraestrutura** (rede, containers, TLS, secrets). A fonte de verdade completa sobre seguranca do projeto — incluindo API, autenticacao, auditoria de imagens e achados do frontend — e `docs/security/SECURITY.md` (ver `docs/development/CONTRIBUTING.md`, secao "Fonte da Verdade"). Nao duplique aqui achados ou politicas que pertencem a esse documento.

## Principios

* Menor privilegio.
* HTTPS obrigatorio.
* Secrets fora do Git.
* Banco sem exposicao publica.
* Backend sem exposicao publica.
* Frontend sem exposicao publica direta.
* Nginx como unico ponto de entrada.

## Controles de borda

Nginx aplica:

* TLS.
* HSTS.
* Headers de seguranca.
* HTTP Basic Auth no dashboard.
* Rate limit no check-in do agente.
* Proxy para frontend/backend.

## Autenticacao

Dois mecanismos, detalhados em `docs/security/AUTH.md`:

```text
Usuarios humanos: login administrativo com Bearer token HMAC SHA-256, RBAC (admin/analyst/viewer)
Agente Windows: header X-Agent-Api-Key, sem RBAC
```

O Nginx ainda aplica HTTP Basic Auth (`.secrets/dashboard.htpasswd`) como camada extra de borda sobre paginas/assets estaticos, mas isso nao substitui o login da aplicacao (ADR-023). O endpoint do agente nao usa Basic Auth nem o login humano porque precisa ser consumido automaticamente por maquinas Windows; a protecao fica na API Key validada pelo backend.

## Segredos

Nunca versionar:

```text
.env.production
.secrets/
*.pem
*.key
```

Secrets gerados na implantacao:

```text
POSTGRES_PASSWORD
AGENT_API_KEY
dashboard.htpasswd
```

## TLS

Certificados:

```text
/etc/letsencrypt/live/itcenter-daniel.chickenkiller.com/fullchain.pem
/etc/letsencrypt/live/itcenter-daniel.chickenkiller.com/privkey.pem
```

## Banco de dados

PostgreSQL:

* Sem porta publica.
* Acessivel apenas pela rede Docker.
* Persistido em volume nomeado.
* Backup em `/opt/itcenter/backups`.

## Riscos residuais

* Nginx ainda mantem Basic Auth como camada extra redundante ao login administrativo (ver ADR-023).
* Banco roda no mesmo host por custo zero.
* Windows Agent ainda nao tem scripts assinados (code-signing pendente na EPIC 16; as demais lacunas de robustez ja foram corrigidas).
* Achados de seguranca do frontend (EPIC 17: token em `localStorage`, ausencia de `middleware.ts` e de security headers) estao detalhados e priorizados em `docs/security/SECURITY.md` — nao duplicados aqui.

## Evolucao recomendada

* Rate limit basico na API.
* Rotacao de secrets (incluindo API Key por agente).
* Assinatura de codigo do agente Windows (EPIC 16, bloqueado por certificado).
* Wazuh.
* Prometheus, Loki e Grafana.
* Reavaliar a necessidade do Basic Auth do Nginx agora que o login administrativo esta em producao (ADR-023).
