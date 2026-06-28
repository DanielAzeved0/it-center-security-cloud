# Troubleshooting de Producao

Este guia lista problemas encontrados e comandos uteis para diagnostico.

## Containers

Listar containers:

```bash
docker ps
docker compose --env-file .env.production -f infra/docker-compose.production.yml ps
```

Logs:

```bash
docker logs itcenter-nginx
docker logs itcenter-frontend
docker logs itcenter-backend
docker logs itcenter-postgres
```

## Preflight falhando

Executar:

```bash
sh infra/scripts/preflight-production.sh
```

Verificar:

* Docker instalado.
* Docker daemon ativo.
* Docker Compose instalado.
* `.env.production` existente.
* `.secrets/dashboard.htpasswd` existente.
* Certificados em `/etc/letsencrypt/live/$DOMAIN_NAME`.
* Portas 80 e 443 livres ou ocupadas pelo Nginx esperado.

## Frontend unhealthy

Sintomas:

```text
frontend: unhealthy
```

Validar internamente:

```bash
docker exec -it itcenter-frontend wget -q -O - http://localhost:3000/
```

Se o problema estiver relacionado ao hostname usado no healthcheck, validar o hostname interno correto do container.

## Backend unhealthy

Validar:

```bash
docker exec -it itcenter-backend wget -q -O - http://127.0.0.1:8000/api/v1/health
docker logs itcenter-backend
```

Causas comuns:

* Banco ainda nao healthy.
* `DATABASE_URL` incorreto.
* Migrations falhando.
* Secrets inconsistentes.

## PostgreSQL unhealthy

Validar:

```bash
docker logs itcenter-postgres
docker exec -it itcenter-postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

Causas comuns:

* Variaveis incorretas em `.env.production`.
* Volume antigo com configuracao divergente.
* Falta de memoria/disco.

## Nginx nao sobe

Validar configuracao:

```bash
docker logs itcenter-nginx
docker exec -it itcenter-nginx nginx -t
```

Causas comuns:

* Certificado ausente.
* `dashboard.htpasswd` sem permissao de leitura.
* `DOMAIN_NAME` diferente do certificado.
* Porta 80/443 ocupada por outro processo.

## Permission denied em dashboard.htpasswd

Sintoma:

```text
Permission denied
```

Corrigir:

```bash
chmod 600 .secrets/dashboard.htpasswd
chmod 700 .secrets
```

Validar owner:

```bash
ls -la .secrets
```

## DNS nao resolve

Testar resolvers publicos:

```bash
dig @8.8.8.8 itcenter-daniel.chickenkiller.com
dig @1.1.1.1 itcenter-daniel.chickenkiller.com
dig @9.9.9.9 itcenter-daniel.chickenkiller.com
```

Se Google, Cloudflare e Quad9 resolvem, mas o provedor local nao resolve, o problema provavelmente e propagacao/cache DNS do provedor.

## Pouca memoria

Sintomas:

* Build falhando.
* Containers reiniciando.
* Processos mortos por OOM.

Validar:

```bash
free -h
docker stats
```

Mitigacao aplicada:

* Criacao de Swap na Oracle VM.

## Dashboard vazio

Isso e esperado enquanto o Windows Agent nao estiver integrado.

O dashboard depende de check-ins em:

```text
POST /api/v1/agent/checkin
```
