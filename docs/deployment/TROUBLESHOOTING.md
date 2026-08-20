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

Checagem consolidada da EPIC 13:

```bash
sh infra/scripts/ops-check.sh
```

O script retorna `FAIL` quando encontrar falha critica em Docker, Compose, containers, certificado TLS ou limites operacionais.

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
docker compose --env-file .env.production -f infra/docker-compose.production.yml exec -T nginx wget -S -O - http://frontend:3000/
```

Se `http://frontend:3000/` responder `200 OK`, o frontend esta acessivel na rede Docker. Evite diagnosticar producao apenas por `127.0.0.1:3000` dentro do container do frontend, pois o runtime standalone do Next.js pode nao estar associado a esse loopback mesmo quando responde pelo hostname do container.

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
* `AUTH_TOKEN_SECRET` ausente ou ainda com placeholder apos a EPIC 12.

Se os logs mostrarem falha de configuracao em producao, validar sem imprimir secrets:

```bash
grep '^AUTH_TOKEN_SECRET=' .env.production | sed 's/=.*/=<definida>/'
grep '^AGENT_API_KEY=' .env.production | sed 's/=.*/=<definida>/'
```

Se `AUTH_TOKEN_SECRET` nao existir, gere um valor forte e adicione em `.env.production`:

```bash
openssl rand -hex 32
```

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
chmod 644 .secrets/dashboard.htpasswd
chmod 700 .secrets
docker compose --env-file .env.production -f infra/docker-compose.production.yml restart nginx
```

Validar owner:

```bash
ls -la .secrets
```

Quando o Nginx nao consegue ler `/etc/nginx/auth/dashboard.htpasswd`, a rota `/` pode retornar:

```text
500 Internal Server Error
open() "/etc/nginx/auth/dashboard.htpasswd" failed (13: Permission denied)
```

O arquivo e montado no container como somente leitura; a permissao `600` para o usuario `ubuntu` no host pode impedir leitura pelo worker do Nginx dentro do container.

## Login administrativo retorna "Invalid credentials" mesmo com senha certa

Sintomas:

```text
{"detail":"Invalid credentials"}
```

em `/login`, para qualquer tentativa, mesmo com email e senha corretos.

Causa comum:

* A tabela `users` esta vazia em producao. Isso acontece quando `backend/create_admin.py` nunca foi executado apos o deploy, ou quando um restore recriou o volume do banco do zero. O script nao roda automaticamente: nao faz parte da imagem Docker do backend nem do `deploy.sh`. Ja aconteceu em producao (INCIDENTE 019 em `POSTMORTEMS.md`).

Validar:

```bash
docker exec -i itcenter-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT count(*) FROM users WHERE role='admin' AND status='active';"
```

Corrigir:

```bash
docker cp backend/create_admin.py itcenter-backend:/app/create_admin.py
docker exec -it itcenter-backend python create_admin.py
```

Executar apos qualquer provisionamento novo do banco (primeiro deploy ou restore que recria o volume `postgres_data` do zero).

## Loop de login / 401 em /me, /machines, /alerts, /security-events apos login bem sucedido

Sintomas:

* O login administrativo funciona (retorna token), mas o navegador volta repetidamente ao prompt de Basic Auth, ou as chamadas seguintes do dashboard falham.
* `/api/backend/api/v1/auth/me`, `/machines`, `/alerts` e `/security-events` retornam `401`.

Causa:

* O Nginx aplica `auth_basic` em `location /` sem excecao. O HTTP permite apenas um cabecalho `Authorization` por requisicao, e chamadas do dashboard com `Authorization: Bearer <token>` perdem, do ponto de vista do Nginx, a credencial Basic Auth que ele exige. Incidente registrado como INCIDENTE 020 em `POSTMORTEMS.md`.

Corrigir:

* Confirmar que a rota `^~ /api/backend/` no Nginx esta isenta de `auth_basic` (ADR-023 em `docs/development/DECISIONS.md`). Qualquer rota nova adicionada sob `location /` que tambem exija Bearer token reproduz o mesmo loop se nao for isenta da mesma forma.

Validar:

```bash
curl -s -o /dev/null -w '%{http_code}' -u admin:SENHA https://itcenter-daniel.chickenkiller.com/api/backend/api/v1/health
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
* Uso pontual de `MIN_MEM_MB=256` no preflight/deploy quando `free -h` confirma swap ativo e a memoria disponivel real fica abaixo de 512MB.

Criar swap:

```bash
sudo rm -f /swapfile
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

## Backup periodico nao executa

Validar cron:

```bash
sudo cat /etc/cron.d/itcenter-postgres-backup
sudo tail -n 100 /opt/itcenter/logs/postgres-backup.log
ls -lh /opt/itcenter/backups
```

Reinstalar agendamento:

```bash
sudo sh infra/scripts/install-backup-cron.sh
```

Causas comuns:

* cron ausente ou parado;
* container `itcenter-postgres` indisponivel;
* permissao insuficiente em `/opt/itcenter/backups`;
* `.env.production` ausente ou com `POSTGRES_DB`/`POSTGRES_USER` incorretos.

## Certificado perto do vencimento

Validar:

```bash
sh infra/scripts/ops-check.sh
```

Testar renovacao:

```bash
TLS_RENEW_DRY_RUN=1 sh infra/scripts/renew-tls.sh
```

Renovar:

```bash
sh infra/scripts/renew-tls.sh
```

Causas comuns:

* porta 80 bloqueada;
* DNS apontando para IP errado;
* webroot `/var/www/certbot` indisponivel;
* container Nginx parado ou unhealthy.

## Docker Scout falhando

Executar gate:

```bash
sh infra/scripts/docker-scout-gate.sh
```

Se falhar:

```bash
docker scout recommendations postgres:16-alpine
docker scout recommendations infra-backend:latest
docker scout recommendations infra-frontend:latest
```

Nao publique imagens de backend ou frontend com CVEs `critical` ou `high` corrigiveis.

### Gate travando ~30 minutos sem terminar (nao e falha de CVE)

Achado em 2026-08-19 (EPIC 36): escanear `infra-backend`/`infra-frontend` (imagens construidas localmente, sem indice pre-computado no Docker Hub como as imagens oficiais) pode esgotar por completo a RAM+swap de `itcenter-edge-01`. Sintomas: `docker scout cves infra-backend:latest` fica parado em "...Indexing" por dezenas de minutos; `free -h` mostra swap perto de 100% de uso; o processo `docker-scout` aparece em estado `D` (uninterruptible sleep) no `ps aux`; SSH fica lento/instavel. Isso nao e uma falha de CVE — o processo tende a morrer sozinho apos ~30 min sem completar, sem derrubar os containers de producao ja rodando (o `up -d` do `deploy.sh` so roda depois do gate, entao nada em producao e afetado enquanto o gate esta preso).

Contorno usado em 2026-08-19: matar o processo (`pkill -9 -f 'docker-scout'` — usar `kill -9 <pid>` direto se `pkill` tambem travar por falta de memoria) e rodar os passos restantes do deploy manualmente pulando o gate (`docker compose up -d` direto, ja com as imagens construidas). Sem correcao definitiva ainda — ver `docs/deployment/KNOWN_ISSUES.md` e EPIC 36 (`docs/development/TASKS.md`).

## Dashboard vazio

Isso e esperado enquanto nenhum Windows Agent tiver enviado check-in com sucesso.

O dashboard depende de check-ins em:

```text
POST /api/v1/agent/checkin
```

Validar no backend/Nginx:

```bash
docker compose --env-file .env.production -f infra/docker-compose.production.yml logs --tail=120 backend nginx
```

Um agente autenticado corretamente deve gerar `POST /api/v1/agent/checkin` com `200 OK`. Se retornar `401`, confira se a chave instalada no agente e exatamente igual a `AGENT_API_KEY` da producao.
