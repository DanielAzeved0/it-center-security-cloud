# Production Setup

Este guia descreve a preparacao de producao do IT Center Security Cloud apos a VM estar disponivel.

## Estrutura operacional

```text
/opt/itcenter/
|-- app/       # clone do repositorio
|-- backups/   # dumps do PostgreSQL
|-- configs/   # configuracoes externas ao Git
|-- runtime/   # estado operacional temporario
|-- scripts/   # automacoes do host
|-- secrets/   # segredos externos ao Git
|-- logs/      # logs operacionais do host
`-- bin/       # atalhos administrativos
```

Criacao manual, quando ainda nao houver bootstrap:

```bash
sudo mkdir -p /opt/itcenter/{app,backups,configs,runtime,scripts,secrets,logs,bin}
sudo chown -R ubuntu:ubuntu /opt/itcenter
```

## Clone do repositorio

O repositorio privado foi clonado via SSH apos configurar a chave da VM no GitHub:

```bash
cd /opt/itcenter/app
git clone git@github.com:DanielAzeved0/it-center-security-cloud.git it-center-security-cloud
cd /opt/itcenter/app/it-center-security-cloud
```

## Variaveis de producao

Criar:

```bash
cp .env.production.example .env.production
```

Gerar valores fortes:

```bash
openssl rand -hex 32
```

Usar esse comando para gerar pelo menos:

```text
POSTGRES_PASSWORD
AGENT_API_KEY
AUTH_TOKEN_SECRET
```

O arquivo `.env.production` nunca deve ser commitado.

## Secrets do dashboard

Criar pasta:

```bash
mkdir -p .secrets
chmod 700 .secrets
```

Criar credencial HTTP Basic:

```bash
docker run --rm httpd:2.4-alpine htpasswd -Bbn admin 'SENHA_FORTE_AQUI' > .secrets/dashboard.htpasswd
chmod 644 .secrets/dashboard.htpasswd
```

## Rede Docker

Todos os servicos de producao usam:

```text
itcenter-network
```

Essa rede isola PostgreSQL, backend e frontend da internet. O Nginx e o unico servico publicado no host.

## Deploy

Com a VM preparada, executar:

```bash
cd /opt/itcenter/app/it-center-security-cloud
sh infra/scripts/deploy.sh
```

O deploy executa:

1. Preflight.
2. Validacao do Compose.
3. Build das imagens.
4. `docker compose up -d`.
5. Espera por healthchecks.
6. Smoke tests.
7. Exibicao de URLs e status final.

## Validacao final

```bash
docker ps
docker compose --env-file .env.production -f infra/docker-compose.production.yml ps
curl -I https://itcenter-daniel.chickenkiller.com
```

Resultado esperado:

```text
postgres: healthy
backend: healthy
frontend: healthy
nginx: healthy
HTTPS: ativo
Dashboard: autenticando com Basic Auth
```
