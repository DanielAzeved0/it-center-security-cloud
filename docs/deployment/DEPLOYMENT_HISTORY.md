# Historico de Implantacao

Este documento registra o processo real de implantacao do IT Center Security Cloud na Oracle Cloud.

## Linha do tempo tecnica

### 1. Docker e Compose

Foi instalado:

```text
Docker Engine
Docker Compose
```

O usuario `ubuntu` foi adicionado ao grupo `docker`.

Validacao:

```bash
docker --version
docker compose version
```

### 2. Acesso ao repositorio privado

Foi configurada chave SSH na Oracle VM e cadastrada no GitHub.

Clone validado:

```bash
git clone git@github.com:DanielAzeved0/it-center-security-cloud.git
```

### 3. Ambiente de producao

Foi criado `.env.production` a partir de `.env.production.example`.

Secrets gerados:

```text
POSTGRES_PASSWORD
AGENT_API_KEY
```

Comando usado:

```bash
openssl rand -hex 32
```

### 4. Credencial administrativa

Foi criada a pasta `.secrets` e o arquivo:

```text
.secrets/dashboard.htpasswd
```

Esse arquivo protege o dashboard com HTTP Basic Auth.

### 5. Compose de producao

Foi validado:

```text
infra/docker-compose.production.yml
```

Servicos:

```text
postgres
backend
frontend
nginx
certbot
```

### 6. Preflight

Foi criado `infra/scripts/preflight-production.sh`.

Validacoes:

* Docker.
* Docker Compose.
* Memoria.
* Disco.
* `.env.production`.
* Secrets.
* Dominio.
* Certificados TLS.
* Volumes.
* Rede Docker.
* Portas.
* Configuracao Docker Compose.

### 7. Deploy

Foi criado `infra/scripts/deploy.sh`.

Responsabilidades:

* Executar preflight.
* Fazer build.
* Executar `docker compose up -d`.
* Aguardar healthchecks.
* Executar smoke tests.
* Mostrar URLs finais.

### 8. Healthcheck do frontend

Foi identificado que o Next.js nao respondia corretamente quando consultado por `127.0.0.1` em determinado contexto de container.

O healthcheck foi ajustado para usar o hostname interno correto do container.

Resultado:

```text
frontend: HEALTHY
```

### 9. DNS

Dominio criado:

```text
itcenter-daniel.chickenkiller.com
```

Apontamento:

```text
147.15.78.220
```

### 10. TLS

Certificado emitido com Let's Encrypt apos ajustes na abertura da porta 80.

Arquivos gerados:

```text
fullchain.pem
privkey.pem
```

### 11. Nginx

Nginx configurado para:

* TLS.
* HTTP para HTTPS.
* Basic Auth.
* Reverse proxy.
* Headers de seguranca.
* Rate limit.
* Proxy para backend.
* Proxy para frontend.

### 12. Validacao final

Todos os containers ficaram saudaveis:

```text
postgres: healthy
backend: healthy
frontend: healthy
nginx: healthy
```

Foram testados:

* Backend `/api/v1/health`.
* Frontend.
* Nginx.

### 13. Problemas encontrados

* DNS da Vivo demorou a propagar.
* Permissao incorreta em `dashboard.htpasswd`.
* Pouca memoria na VM exigiu criacao de Swap.

### 14. Estado final

```text
Infraestrutura: funcional
HTTPS: funcional
Nginx: funcional
Dashboard: funcional
Backend: funcional
PostgreSQL: funcional
Windows Agent: pendente de integracao
```
