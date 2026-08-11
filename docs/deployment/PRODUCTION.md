# PRODUCTION.md

# Estratégia Oficial de Deploy

## Objetivo

Definir como o IT Center Security Cloud será publicado em produção.

---

# Ambiente Oficial

Oracle Cloud Free Tier

Motivo:

* Gratuito
* Confiável
* Ideal para MVP
* Sem custo inicial

---

# Nó de Borda do MVP

Nome:

```text
itcenter-edge-01
```

Sistema operacional:

```text
Ubuntu Server 24.04 LTS
```

Estrutura oficial do host:

```text
/opt/itcenter/
|-- app/       # clone do repositorio e arquivos de deploy versionados
|-- backups/   # dumps e artefatos de backup
|-- configs/   # configuracoes operacionais externas ao Git, quando necessario
|-- runtime/   # estado operacional temporario do host
|-- scripts/   # automacoes operacionais instaladas no host
|-- secrets/   # segredos operacionais externos ao Git, quando necessario
|-- logs/      # logs operacionais do host; containers devem priorizar stdout/stderr
`-- bin/       # wrappers ou atalhos administrativos locais
```

No MVP, o repositório deve ficar em `/opt/itcenter/app/it-center-security-cloud`. Os arquivos `.env.production` e `.secrets/dashboard.htpasswd` continuam dentro desse diretório da aplicação porque o Compose e o preflight usam caminhos relativos ao repositório. O diretório `/opt/itcenter/secrets` fica reservado para uma próxima evolução, quando esses caminhos forem externalizados sem quebrar o contrato atual.

---

# Topologia de Rede

```text
Internet
    ↓
IPv4 público
    ↓
Oracle Cloud VCN (10.0.0.0/16)
    ├── Subnet pública (10.0.0.0/24)
    │       └── itcenter-edge-01
    │             └── Docker Compose: nginx, frontend, backend, postgres
    └── Subnet privada (10.0.1.0/24)
            └── Reservada para futura separação dos serviços
```

No MVP, a instância `itcenter-edge-01` usa a subnet pública e recebe um IPv4 público. PostgreSQL, FastAPI e Next.js não recebem portas publicadas no host: somente o Nginx publica 80 e 443. A subnet privada é criada desde o início para suportar a evolução sem alterar o endereço público ou o papel do nó de borda.

---

# Containers

## Nginx

Responsável por:

* HTTPS
* Proxy Reverso
* Certificados

---

## Frontend

Tecnologia:

Next.js

Porta Interna:

3000

---

## Backend

Tecnologia:

FastAPI

Porta Interna:

8000

---

## Banco

Tecnologia:

PostgreSQL

Porta Interna:

5432

---

# Docker Compose

Containers:

* nginx
* frontend
* backend
* postgres

Rede de produção:

```text
itcenter-network
```

Todos os containers de produção entram nessa rede Docker explícita. Somente o `nginx` publica portas no host. `frontend`, `backend` e `postgres` se comunicam por DNS interno do Docker.

Volumes e mounts:

* `postgres_data`: volume nomeado para dados persistentes do PostgreSQL.
* `../backend/migrations:/migrations:ro`: bind mount somente leitura para migrations usadas pelo banco/backend.
* `./nginx/nginx.conf.template:/etc/nginx/templates/default.conf.template:ro`: template de configuração do Nginx.
* `../.secrets/dashboard.htpasswd:/etc/nginx/auth/dashboard.htpasswd:ro`: credencial Basic Auth fora do Git.
* `/etc/letsencrypt:/etc/letsencrypt:ro`: certificados TLS para leitura pelo Nginx.
* `/var/www/certbot:/var/www/certbot:ro`: webroot do Certbot para validação HTTP.

Exceção operacional: o serviço `certbot`, usado apenas no profile `maintenance`, monta `/etc/letsencrypt` e `/var/www/certbot` com escrita porque precisa emitir e renovar certificados. O Nginx continua consumindo esses mesmos caminhos somente leitura.

Logs:

* Containers devem registrar em `stdout`/`stderr`.
* Não criar volume nomeado para logs no MVP.
* A coleta futura por Loki/Promtail ou outro agente deve ler os logs do Docker/host.

---

# Produção

O arquivo de produção é separado do ambiente local:

```text
infra/docker-compose.production.yml
```

Ele expõe somente o Nginx nas portas `80` e `443`. PostgreSQL, FastAPI e Next.js existem apenas na rede Docker interna e não possuem portas publicadas no host.

## Pré-requisitos da VM Oracle

* VCN `10.0.0.0/16` criada na Oracle Cloud.
* Subnet pública `10.0.0.0/24`, com Internet Gateway e rota `0.0.0.0/0` para esse gateway.
* Subnet privada `10.0.1.0/24`, sem IP público e reservada para uso futuro.
* Instância `itcenter-edge-01` com Ubuntu Server 24.04 LTS atualizado, na subnet pública e com IPv4 público.
* Docker Engine e Docker Compose Plugin instalados.
* Diretórios operacionais criados em `/opt/itcenter`.
* Repositório clonado em `/opt/itcenter/app/it-center-security-cloud`.
* Firewall da Oracle Cloud e UFW liberando somente `22` (restrito ao IP administrativo), `80` e `443`.
* Registro DNS `A` de `DOMAIN_NAME` apontando para o IP público da VM.
* Acesso SSH por chave; login por senha e login direto do root desabilitados.

Nota: a VCN, as subnets, a security list e a instância `itcenter-edge-01` já são geridas via Terraform (`infra/terraform/`, ADR-024), introduzido por `terraform import` dos recursos existentes em produção, sem destroy/recreate. Qualquer mudança nesses recursos deve passar por `terraform plan`/`apply` revisado — não mais pelo Console Oracle manualmente. Ver `infra/terraform/README.md` e `docs/architecture/IAC.md`.

## Bootstrap versionado do Edge Node

A preparacao inicial do host passara a ser feita por scripts versionados. A proposta esta documentada em:

```text
docs/deployment/BOOTSTRAP.md
```

Estrutura planejada:

```text
infra/
└── bootstrap/
    ├── 01-system.sh
    ├── 02-packages.sh
    ├── 03-directories.sh
    ├── 04-docker.sh
    ├── 05-firewall.sh
    └── bootstrap.sh
```

Neste momento, esta etapa esta apenas documentada. Os scripts devem ser criados em uma etapa futura. O bootstrap nao deve instalar a aplicacao imediatamente; ele deve preparar a VM, instalar dependencias de host e criar `/opt/itcenter`. Clone do repositorio, `.env.production`, Compose, HTTPS, Certbot e preflight continuam na etapa de deploy abaixo.

## Segredos e acesso administrativo

Se o bootstrap ainda nao tiver sido executado, prepare a estrutura operacional manualmente:

```bash
sudo mkdir -p /opt/itcenter/{app,backups,configs,runtime,scripts,secrets,logs,bin}
sudo chown -R ubuntu:ubuntu /opt/itcenter
```

Depois acesse o repositorio clonado em `/opt/itcenter/app/it-center-security-cloud`:

```bash
cd /opt/itcenter/app/it-center-security-cloud
```

Na raiz do repositório, na VM:

```bash
cp .env.production.example .env.production
mkdir -p .secrets /var/www/certbot
chmod 700 .secrets
```

Edite `.env.production` com um domínio real e valores aleatórios distintos. Não reutilize `change-me` nem mantenha os valores `REPLACE_WITH...`. Para evitar caracteres que exigiriam codificação na `DATABASE_URL`, uma opção simples é gerar os segredos com `openssl rand -hex 32`; o valor de `POSTGRES_PASSWORD` deve ser reproduzido literalmente na URL. Gere valores distintos para `POSTGRES_PASSWORD`, `AGENT_API_KEY` e `AUTH_TOKEN_SECRET`.

Crie a credencial do dashboard com bcrypt. O arquivo não deve ser commitado:

```bash
docker run --rm httpd:2.4-alpine htpasswd -Bbn admin 'SENHA_FORTE_AQUI' > .secrets/dashboard.htpasswd
chmod 644 .secrets/dashboard.htpasswd
chmod 600 .env.production
```

O Nginx exige essa credencial para o dashboard e para as chamadas administrativas proxificadas pelo Next.js. Como esse arquivo e montado somente leitura no container, ele precisa ser legivel pelo worker do Nginx. Permissao `600` no host pode gerar `500 Internal Server Error` com `Permission denied`; use `644` para `.secrets/dashboard.htpasswd` e mantenha `.env.production` com `600`. O check-in do agente continua autenticado por `X-Agent-Api-Key`; use no agente a mesma chave definida em `AGENT_API_KEY`.

## Certificado TLS inicial

Com o DNS já propagado e as portas 80/443 liberadas, emita o certificado antes do primeiro `up`:

```bash
sudo docker run --rm -p 80:80 \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/lib/letsencrypt:/var/lib/letsencrypt \
  certbot/certbot:v5.7.0 certonly --standalone \
  -d SEU_DOMINIO --email SEU_EMAIL --agree-tos --no-eff-email
```

Substitua `SEU_DOMINIO` pelo mesmo valor de `DOMAIN_NAME`. Não publique com certificado autoassinado nem HTTP aberto.

## Validar e publicar

```bash
sh infra/scripts/deploy.sh
curl --fail --user admin:SENHA_FORTE_AQUI https://SEU_DOMINIO/
```

O `deploy.sh` executa preflight, valida o Compose, faz build das imagens, sobe os containers, aguarda healthchecks e executa smoke tests internos. O preflight falha se Docker/Compose estiverem ausentes, se o host tiver pouco recurso, se segredos ainda forem placeholders, se a credencial administrativa não existir, se o certificado estiver ausente, se o Compose for inválido ou se portas essenciais estiverem ocupadas por outro processo.

Em instancias Oracle Free Tier com pouca RAM, crie swap antes do deploy. O preflight mede `MemAvailable` e nao soma swap; quando a VM ja tiver swap ativo e os containers estiverem saudaveis, o limite pode ser reduzido explicitamente:

```bash
MIN_MEM_MB=256 sh infra/scripts/preflight-production.sh
MIN_MEM_MB=256 sh infra/scripts/deploy.sh
```

Use esse override somente depois de validar `free -h`.

Smoke tests esperados:

```bash
docker compose --env-file .env.production -f infra/docker-compose.production.yml exec -T backend wget -q -O /dev/null http://127.0.0.1:8000/api/v1/health
docker compose --env-file .env.production -f infra/docker-compose.production.yml exec -T nginx wget -q -O /dev/null http://frontend:3000/
docker compose --env-file .env.production -f infra/docker-compose.production.yml exec -T nginx wget -q -O /dev/null http://127.0.0.1/healthz
```

O frontend deve ser validado pelo DNS interno Docker (`frontend:3000`) a partir do Nginx. Em algumas imagens standalone do Next.js, `127.0.0.1:3000` dentro do proprio container pode recusar conexao mesmo com o servico acessivel pela rede Docker.

## GitHub Actions

O projeto usa GitHub Actions para automatizar validacoes e permitir deploy manual em producao sem versionar secrets da aplicacao.

Workflows:

```text
.github/workflows/ci.yml
.github/workflows/deploy-production.yml
```

O workflow `CI` executa:

* testes do backend com PostgreSQL de servico;
* build do dashboard Next.js;
* validacao do Docker Compose local e do Compose de producao com placeholders temporarios.

O workflow `Deploy Production` e manual (`workflow_dispatch`) e deve ser executado somente apos o CI passar. Ele acessa a VM por SSH, atualiza o repositorio para o ref selecionado, executa backup e chama o deploy versionado:

```bash
sh infra/scripts/backup.sh
MIN_MEM_MB=256 sh infra/scripts/deploy.sh
```

A atualizacao do codigo na VM usa o `GITHUB_TOKEN` temporario do proprio workflow com permissao `contents: read`, buscando o ref por HTTPS. Portanto, a VM nao precisa ter uma deploy key propria para acessar o repositorio GitHub durante esse deploy.

Secrets necessarios no GitHub:

```text
PROD_SSH_HOST
PROD_SSH_USER
PROD_SSH_PRIVATE_KEY
PROD_APP_DIR
PROD_SSH_PORT
```

`PROD_SSH_PORT` e opcional quando SSH usa a porta `22`. `PROD_APP_DIR` deve apontar para:

```text
/opt/itcenter/app/it-center-security-cloud
```

Os secrets da aplicacao continuam fora do GitHub Actions e permanecem na VM:

```text
.env.production
.secrets/dashboard.htpasswd
/etc/letsencrypt
```

O deploy automatico em todo push nao esta habilitado neste momento. A politica atual e CI automatico e deploy manual com controle operacional.

### Registro do rollout do GitHub Actions

Status em 2026-06-30:

* secrets de SSH de producao cadastrados em `Settings > Secrets and variables > Actions`;
* workflow `CI` executado com sucesso no GitHub Actions, cobrindo backend tests, frontend build e compose validation;
* erro de sintaxe no heredoc do `deploy-production.yml` corrigido antes do primeiro deploy;
* dependencia `httpx` adicionada ao backend para suportar `fastapi.testclient.TestClient` no ambiente do CI.
* deploy ajustado para buscar o codigo via HTTPS com `GITHUB_TOKEN` temporario, evitando dependencia de chave SSH da VM para o GitHub.
* workflow `Deploy Production` executado manualmente com sucesso;
* backup PostgreSQL criado antes do deploy;
* build das imagens `infra-backend` e `infra-frontend` concluido;
* containers `postgres`, `backend`, `frontend` e `nginx` validados como saudaveis;
* smoke tests de producao aprovados;
* dashboard publicado validado no navegador sem bug visual reportado.

Evidencia registrada em:

```text
docs/deployment/DEPLOYMENT_HISTORY.md
docs/development/TASKS.md
```

## Rollback

Antes de qualquer rollback, faça backup do banco. O rollback preserva o volume `postgres_data` e troca apenas a versão da aplicação pelo Git ref informado:

```bash
sh infra/scripts/backup.sh
sh infra/scripts/rollback.sh HEAD~1
```

Use um commit, tag ou branch estável no lugar de `HEAD~1` quando houver uma versão homologada.

## Backup e restore

Backup manual:

```bash
sh infra/scripts/backup.sh
```

Variáveis opcionais:

```text
BACKUP_DIR=/opt/itcenter/backups
RETENTION_DAYS=7
```

Instalar backup periodico diario na VM:

```bash
sudo sh infra/scripts/install-backup-cron.sh
```

Customizacao:

```bash
sudo BACKUP_HOUR=3 BACKUP_MINUTE=0 RETENTION_DAYS=14 sh infra/scripts/install-backup-cron.sh
```

Restore exige confirmação explícita para evitar sobrescrita acidental:

```bash
ITCENTER_RESTORE_CONFIRM=YES sh infra/scripts/restore.sh /opt/itcenter/backups/itcenter-postgres-YYYYMMDDTHHMMSSZ.sql.gz
```

## Renovação de certificado e rollback

Renove mensalmente (ou agende via systemd/cron) e recarregue o Nginx após a renovação:

```bash
TLS_RENEW_DRY_RUN=1 sh infra/scripts/renew-tls.sh
sh infra/scripts/renew-tls.sh
```

Antes de qualquer atualização, faça backup do PostgreSQL. Migrations devem ser sempre retrocompatíveis, pois não há rollback automático de schema.

## Rotina operacional semanal

Runbook oficial:

```text
docs/deployment/WEEKLY_OPERATIONS.md
```

Checagem consolidada:

```bash
sh infra/scripts/ops-check.sh
```

O script verifica disco, memoria, Compose, containers, certificado TLS e backup recente. Ele retorna `FAIL` e codigo diferente de zero quando houver falha critica.

---

# Ambiente Local com Docker Compose

O ambiente local usa o mesmo Docker Compose como base operacional, mas sem Nginx.

Arquivo:

```text
infra/docker-compose.yml
```

Servicos locais:

```text
postgres
backend
frontend
```

Fluxo de inicializacao:

```text
1. postgres inicia.
2. Compose aguarda healthcheck do postgres.
3. backend executa apply_migrations.py.
4. backend inicia FastAPI em 0.0.0.0:8000.
5. Compose aguarda healthcheck do backend.
6. frontend inicia Next.js em 0.0.0.0:3000.
```

Comandos para subir, parar, ver status/logs e as URLs locais ficam documentados em `infra/README.md`, fonte única desses comandos para não manter duas cópias divergentes.

---

# Imagens Locais

## Backend

Arquivo:

```text
backend/Dockerfile
```

Responsabilidades:

* Instalar dependencias Python.
* Copiar `app/`, `migrations/` e `apply_migrations.py`.
* Aplicar migrations antes de iniciar Uvicorn.
* Expor porta interna 8000.

## Frontend

Arquivo:

```text
frontend/dashboard/Dockerfile
```

Responsabilidades:

* Instalar dependencias com `npm ci`.
* Aplicar patch de seguranca do `picomatch` empacotado pelo Next.js.
* Executar `npm run build`.
* Gerar runtime standalone do Next.js.
* Remover `npm` global da imagem final.
* Iniciar o servidor standalone com `node server.js`.
* Expor porta interna 3000.

---

# Variáveis de Ambiente

Utilizar:

.env

Nunca armazenar:

* Senhas
* Tokens
* Chaves

no GitHub.

---

# Domínio

Domínio real em uso:

```text
itcenter-daniel.chickenkiller.com
```

IP público associado — **efêmero** (não reservado, decisão consciente de não travar a associação a um IP fixo neste estágio do MVP; ver `docs/architecture/IAC.md`):

```text
147.15.78.220
```

Detalhes de DNS, Certbot e TLS ficam em `docs/deployment/HTTPS.md`.

---

# Monitoramento da VM

Monitorar:

* CPU
* RAM
* Disco
* Containers

---

# Gate de Seguranca das Imagens

Antes de publicar ou considerar um build pronto para ambiente externo, executar o gate Docker Scout:

```bash
sh infra/scripts/docker-scout-gate.sh
```

Quando houver vulnerabilidade critica ou alta, consultar recomendacoes:

```powershell
docker scout recommendations postgres:16-alpine
docker scout recommendations infra-backend:latest
docker scout recommendations infra-frontend:latest
```

Criterio:

* Backend e frontend nao devem seguir para deploy externo com CVE critical/high corrigivel.
* PostgreSQL com CVE residual em imagem oficial pode continuar apenas em ambiente local/laboratorio, documentado como P1 em `docs/security/SECURITY.md`, ate existir tag oficial corrigida.
* O banco nunca deve ser exposto publicamente.

Build limpo recomendado apos mudancas de imagem/dependencia:

```powershell
cd "<caminho-local>\it-center-security-cloud"
docker compose -f infra/docker-compose.yml build --no-cache backend frontend
docker compose -f infra/docker-compose.yml up -d
```
