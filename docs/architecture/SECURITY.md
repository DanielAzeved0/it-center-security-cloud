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
* Rate limit no check-in do agente (Nginx, `limit_req`) — implementado.
* Proxy para frontend/backend.

## Autenticacao

Tres mecanismos, detalhados em `docs/security/AUTH.md`:

```text
Usuarios humanos: login administrativo com Bearer token HMAC SHA-256, RBAC (admin/analyst/viewer)
Agente Windows (classe): header X-Agent-Api-Key, sem RBAC, compartilhado por todos os agentes
Agente Windows (individuo): agent_secret por maquina, trust-on-first-use (agent_secret_hash, migration 009, ADR-036) - segunda camada sobre a X-Agent-Api-Key, fecha a janela de personificacao de maquina (EPIC 28-A)
```

O Nginx ainda aplica HTTP Basic Auth (`.secrets/dashboard.htpasswd`) como camada extra de borda sobre paginas/assets estaticos, mas isso nao substitui o login da aplicacao (ADR-023). Os endpoints do agente nao usam Basic Auth nem o login humano porque precisam ser consumidos automaticamente por maquinas Windows; a protecao fica na API Key (e no agent_secret, para o check-in) validados pelo backend. Essa isencao de Basic Auth cobre os 3 endpoints do agente em `infra/nginx/nginx.conf.template`: `POST /api/v1/agent/checkin`, e desde 2026-08-19 (EPIC 37) tambem `GET /api/v1/agent/manifest` e `GET /api/v1/agent/download` (blocos `location =` dedicados, espelhando o de `/agent/checkin`) — validado localmente ponta a ponta contra o backend real (401 do FastAPI, nao do Nginx, para os 2 endpoints novos sem `X-Agent-Api-Key`; 401 do Nginx preservado para as demais rotas). **Ainda nao deployado em `itcenter-edge-01`** (ver `docs/deployment/KNOWN_ISSUES.md`).

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
* EPIC 16 (hardening do agente Windows) concluida: scripts assinados com certificado Authenticode self-signed e Tarefa Agendada com `ExecutionPolicy AllSigned` (ADR-031), alem das demais lacunas de robustez ja corrigidas.
* EPIC 17 (hardening do frontend) concluida: cookie `httpOnly` de sessao, `middleware.ts`, CSP e demais itens corrigidos — detalhes em `docs/security/SECURITY.md`, nao duplicados aqui.

## Evolucao recomendada

* Rate limit geral nas demais rotas da API (hoje implementado apenas no check-in do agente, via Nginx `limit_req`).
* Rotacao de secrets (incluindo API Key por agente).
* Wazuh.
* Prometheus, Loki e Grafana para observabilidade da infraestrutura (ja com plano formal em ADR-030/EPIC 21).
* Reavaliar a necessidade do Basic Auth do Nginx agora que o login administrativo esta em producao (ADR-023).
