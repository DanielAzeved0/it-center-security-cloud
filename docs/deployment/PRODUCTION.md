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

O `deploy.sh` executa preflight, valida o Compose, faz build das imagens, roda o gate de CVE do Docker Scout (`infra/scripts/docker-scout-gate.sh`), sobe os containers, aguarda healthchecks e executa smoke tests internos. O preflight falha se Docker/Compose estiverem ausentes, se o host tiver pouco recurso, se segredos ainda forem placeholders, se a credencial administrativa não existir, se o certificado estiver ausente, se o Compose for inválido ou se portas essenciais estiverem ocupadas por outro processo. O gate de CVE roda entre o `build` e o `up -d`: como o script usa `set -eu`, uma falha do gate (CVE critical/high nas imagens configuradas) aborta o deploy automaticamente antes de qualquer container novo subir — os containers antigos continuam rodando sem interrupção (EPIC 29, 2026-08-17).

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

O primeiro deploy via `Deploy Production` (2026-06-30) esta registrado em `docs/deployment/DEPLOYMENT_HISTORY.md` ("2026-06-30 - Deploy manual via GitHub Actions"), fonte de verdade dessa linha do tempo.

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

### Comportamento interno do backup (EPIC 29, 2026-08-17)

`infra/scripts/backup.sh` roda em `sh` puro (`set -eu`, sem `pipefail`/`PIPESTATUS`), então o `pg_dump` nunca é ligado por pipe direto ao `gzip`: o dump vai primeiro para um arquivo intermediário oculto (`$BACKUP_DIR/.itcenter-postgres-<timestamp>.sql`) via redirecionamento simples, o que permite capturar o exit code real do `pg_dump`/`docker exec`. Sequência de validação, na ordem:

1. Se o `pg_dump` falhar (Postgres fora do ar, credencial errada, disco cheio) ou o dump intermediário ficar vazio, o script remove o arquivo intermediário, imprime um erro claro em `stderr` e sai com código diferente de zero — **sem gerar `.sql.gz` e sem rodar a retenção**.
2. Só com o dump validado o script comprime para o `.sql.gz` final, remove o intermediário e aplica `chmod 600`.
3. O `.sql.gz` final passa por `gzip -t`; se falhar, o arquivo é removido e o script sai com erro, também sem rodar a retenção.
4. A retenção (`find ... -delete`) só roda depois que as duas validações acima passarem.

Na prática: se `sh infra/scripts/backup.sh` sair com código diferente de zero, nenhum backup novo foi criado e nenhum backup antigo foi apagado — o operador pode tentar de novo com segurança depois de corrigir a causa raiz (ver mensagem em `stderr`).

Restore exige confirmação explícita para evitar sobrescrita acidental:

```bash
ITCENTER_RESTORE_CONFIRM=YES sh infra/scripts/restore.sh /opt/itcenter/backups/itcenter-postgres-YYYYMMDDTHHMMSSZ.sql.gz
```

### Comportamento interno do restore (EPIC 29, 2026-08-17)

`infra/scripts/restore.sh` valida o backup **antes** de tocar no schema do banco, na ordem:

1. `gzip -t` no arquivo de backup informado. Se falhar (arquivo truncado/corrompido), o script aborta com erro em `stderr` sem rodar `DROP SCHEMA` — o banco atual permanece intacto.
2. Descompressão para um arquivo intermediário oculto (`.itcenter-restore-<pid>.sql`, no mesmo diretório do backup) via redirecionamento simples (não mais pipe), com checagem do exit code do `gzip` e do tamanho do arquivo resultante. Se falhar, o intermediário é removido e o script aborta — de novo, sem tocar no schema.
3. Só depois dessas duas validações o script roda `DROP SCHEMA public CASCADE; CREATE SCHEMA public;` e restaura a partir do arquivo intermediário (`psql ... < arquivo`, não mais pipe). As duas chamadas de `psql` usam `-v ON_ERROR_STOP=1`, então qualquer erro de SQL durante o restore aborta o script imediatamente em vez de ser silenciosamente ignorado.
4. Verificação pós-restore: o script conta quantas das 5 tabelas centrais (`machines`, `users`, `audit_logs`, `alerts`, `security_events`) existem em `information_schema.tables` no schema `public`. Se o resultado for menor que 5, o script imprime um erro claro em `stderr` e sai com código diferente de zero — a mensagem "Restore concluido" só aparece quando as 5 tabelas são confirmadas, e a mensagem inclui a contagem (`Restore concluido: 5 das 5 tabelas centrais confirmadas em information_schema.tables.`).

Se o restore reportar erro em qualquer uma dessas etapas, trate como restore não confiável: não assuma que os dados voltaram só porque o comando terminou — confira a mensagem em `stderr` antes de liberar o ambiente.

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

`infra/scripts/deploy.sh` chama `docker-scout-gate.sh` automaticamente entre o `build` e o `up -d` (EPIC 29, 2026-08-17) — deixou de depender de um humano lembrar de rodar manualmente antes de publicar. Uma falha do gate (CVE critical/high em alguma imagem de `ITCENTER_SCOUT_IMAGES`) aborta o deploy antes de qualquer container novo subir, graças ao `set -eu` já ativo no script.

**Ressalva importante (achado de 2026-08-19):** "containers antigos continuam rodando" é verdade, mas incompleto — no fluxo real de `deploy-production.yml`, o `git checkout --force FETCH_HEAD` já roda **antes** do `deploy.sh` (e portanto antes do gate). Uma falha do gate deixa o *checkout* já avançado para o novo commit, mesmo com os containers ainda na versão antiga — exatamente a defasagem de 2 dias descoberta nesta data (ver `docs/deployment/DEPLOYMENT_HISTORY.md`). Além disso, o gate pode falhar não só por CVE, mas por travar completamente por falta de RAM ao escanear `infra-backend`/`infra-frontend` (imagens locais, sem índice pré-computado — ver `docs/deployment/KNOWN_ISSUES.md` e EPIC 36), deixando o deploy pendurado em vez de abortar rápido.

Para rodar o gate isoladamente (fora de um deploy, por exemplo durante desenvolvimento local ou investigação de CVE):

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
