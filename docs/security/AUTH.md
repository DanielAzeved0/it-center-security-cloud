# Autenticacao

Este documento descreve os mecanismos de autenticacao atuais do IT Center Security Cloud.

## Dashboard

No MVP, o dashboard e protegido por HTTP Basic Auth no Nginx.

Arquivo:

```text
.secrets/dashboard.htpasswd
```

Esse arquivo nao deve ser commitado.

Criacao:

```bash
mkdir -p .secrets
docker run --rm httpd:2.4-alpine htpasswd -Bbn admin 'SENHA_FORTE_AQUI' > .secrets/dashboard.htpasswd
chmod 700 .secrets
chmod 644 .secrets/dashboard.htpasswd
```

O arquivo `dashboard.htpasswd` precisa ser legivel pelo worker do Nginx dentro do container. Por isso, em producao, use `644` no arquivo e mantenha a pasta `.secrets` com `700`.

## Agente Windows

O agente usa API Key no header:

```text
X-Agent-Api-Key
```

O valor vem de:

```text
AGENT_API_KEY
```

Esse valor fica em `.env.production` no servidor e nunca deve ser versionado.

## Fora do escopo atual

Ainda nao existe:

* login com usuarios;
* sessoes;
* RBAC;
* auditoria completa de usuarios.

Esses controles pertencem a fase futura de governanca.
