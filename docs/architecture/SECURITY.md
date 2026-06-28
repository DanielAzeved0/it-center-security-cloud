# Security Architecture

Este documento descreve os controles de seguranca aplicados na infraestrutura.

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

Dashboard:

```text
HTTP Basic Auth
.secrets/dashboard.htpasswd
```

Agente:

```text
X-Agent-Api-Key
```

O endpoint do agente nao usa Basic Auth porque precisa ser consumido automaticamente por maquinas Windows. A protecao fica na API Key validada pelo backend.

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

* Dashboard ainda usa Basic Auth no MVP.
* Banco roda no mesmo host por custo zero.
* Windows Agent ainda precisa evoluir assinatura, criptografia e retry inteligente.

## Evolucao recomendada

* Login com usuarios.
* RBAC.
* Auditoria.
* Rotacao de secrets.
* Wazuh.
* Prometheus, Loki e Grafana.
