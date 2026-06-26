# DEPLOYMENT.md

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
├── app/       # clone do repositório e arquivos de deploy versionados
├── backups/   # dumps e artefatos de backup
├── configs/   # configurações operacionais externas ao Git, quando necessário
├── logs/      # logs operacionais do host; containers devem priorizar stdout/stderr
├── scripts/   # automações operacionais do host
└── secrets/   # segredos operacionais externos ao Git, quando necessário
```

No MVP, o repositório deve ficar em `/opt/itcenter/app`. Os arquivos `.env.production` e `.secrets/dashboard.htpasswd` continuam dentro desse diretório da aplicação porque o Compose e o preflight usam caminhos relativos ao repositório. O diretório `/opt/itcenter/secrets` fica reservado para uma próxima evolução, quando esses caminhos forem externalizados sem quebrar o contrato atual.

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
* Repositório clonado em `/opt/itcenter/app`.
* Firewall da Oracle Cloud e UFW liberando somente `22` (restrito ao IP administrativo), `80` e `443`.
* Registro DNS `A` de `DOMAIN_NAME` apontando para o IP público da VM.
* Acesso SSH por chave; login por senha e login direto do root desabilitados.

## Segredos e acesso administrativo

Prepare a estrutura operacional e acesse o repositório:

```bash
sudo mkdir -p /opt/itcenter/{app,backups,configs,logs,scripts,secrets}
sudo chown -R ubuntu:ubuntu /opt/itcenter
cd /opt/itcenter/app
```

Na raiz do repositório, na VM:

```bash
cp .env.production.example .env.production
mkdir -p .secrets /var/www/certbot
chmod 700 .secrets
```

Edite `.env.production` com um domínio real e valores aleatórios distintos. Não reutilize `change-me` nem mantenha os valores `REPLACE_WITH...`. Para evitar caracteres que exigiriam codificação na `DATABASE_URL`, uma opção simples é gerar ambos os segredos com `openssl rand -hex 32`; o valor de `POSTGRES_PASSWORD` deve ser reproduzido literalmente na URL.

Crie a credencial do dashboard com bcrypt. O arquivo não deve ser commitado:

```bash
docker run --rm httpd:2.4-alpine htpasswd -Bbn admin 'SENHA_FORTE_AQUI' > .secrets/dashboard.htpasswd
chmod 600 .secrets/dashboard.htpasswd .env.production
```

O Nginx exige essa credencial para o dashboard e para as chamadas administrativas proxificadas pelo Next.js. O check-in do agente continua autenticado por `X-Agent-Api-Key`; use no agente a mesma chave definida em `AGENT_API_KEY`.

## Certificado TLS inicial

Com o DNS já propagado e as portas 80/443 liberadas, emita o certificado antes do primeiro `up`:

```bash
sudo docker run --rm -p 80:80 \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/lib/letsencrypt:/var/lib/letsencrypt \
  certbot/certbot:v4.21.0 certonly --standalone \
  -d SEU_DOMINIO --email SEU_EMAIL --agree-tos --no-eff-email
```

Substitua `SEU_DOMINIO` pelo mesmo valor de `DOMAIN_NAME`. Não publique com certificado autoassinado nem HTTP aberto.

## Validar e publicar

```bash
chmod +x infra/scripts/preflight-production.sh
infra/scripts/preflight-production.sh
docker compose --env-file .env.production -f infra/docker-compose.production.yml up -d --build
docker compose --env-file .env.production -f infra/docker-compose.production.yml ps
curl --fail --user admin:SENHA_FORTE_AQUI https://SEU_DOMINIO/
```

O preflight falha se segredos ainda forem placeholders, se a credencial administrativa não existir, se o certificado estiver ausente ou se o Compose for inválido.

## Renovação de certificado e rollback

Renove mensalmente (ou agende via systemd/cron) e recarregue o Nginx após a renovação:

```bash
docker compose --env-file .env.production -f infra/docker-compose.production.yml --profile maintenance run --rm certbot renew --webroot -w /var/www/certbot
docker compose --env-file .env.production -f infra/docker-compose.production.yml exec nginx nginx -s reload
```

Antes de qualquer atualização, faça backup do PostgreSQL. Para rollback da aplicação, retorne ao commit/imagem anterior e execute `up -d`; migrations devem ser sempre retrocompatíveis, pois não há rollback automático de schema.

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

Comando principal:

```powershell
cd "C:\Users\Famili Azevedo\Desktop\it-center-security-cloud"
docker compose -f infra/docker-compose.yml up --build
```

Em segundo plano:

```powershell
cd "C:\Users\Famili Azevedo\Desktop\it-center-security-cloud"
docker compose -f infra/docker-compose.yml up --build -d
```

URLs locais:

```text
Dashboard: http://127.0.0.1:3000
Backend:   http://127.0.0.1:8000/api/v1/health
Postgres:  127.0.0.1:5432
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

Parar:

```powershell
cd "C:\Users\Famili Azevedo\Desktop\it-center-security-cloud"
docker compose -f infra/docker-compose.yml down
```

Parar e remover dados locais:

```powershell
cd "C:\Users\Famili Azevedo\Desktop\it-center-security-cloud"
docker compose -f infra/docker-compose.yml down -v
```

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
* Remover `npm` global da imagem final.
* Iniciar Next.js em modo production diretamente com `node`.
* Expor porta interna 3000.

---

# HTTPS

Ferramenta:

Let's Encrypt

Cliente:

Certbot

Objetivo:

Criptografar comunicação.

---

# Firewall

Liberar apenas:

80
443

Bloquear:

5432

8000

3000

externamente.

---

# Backups

Banco:

Backup diário.

Retenção:

7 dias.

Local:

Volume Docker + Storage Oracle.

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

Inicial:

IP público Oracle

Futuro:

itcentercloud.com

---

# Monitoramento da VM

Monitorar:

* CPU
* RAM
* Disco
* Containers

---

# Critério de Produção

Ambiente será considerado pronto quando:

* HTTPS ativo
* Banco funcionando
* Backend funcionando
* Frontend funcionando
* Backup configurado
* Firewall configurado
* Docker Compose operacional

---

# Gate de Seguranca das Imagens

Antes de publicar ou considerar um build pronto para ambiente externo, executar Docker Scout nas imagens finais:

```powershell
docker scout cves postgres:16-alpine --only-severity critical,high
docker scout cves infra-backend:latest --only-severity critical,high
docker scout cves infra-frontend:latest --only-severity critical,high
```

Quando houver vulnerabilidade critica ou alta, consultar recomendacoes:

```powershell
docker scout recommendations postgres:16-alpine
docker scout recommendations infra-backend:latest
docker scout recommendations infra-frontend:latest
```

Criterio:

* Backend e frontend nao devem seguir para deploy externo com CVE critical/high corrigivel.
* PostgreSQL com CVE residual em imagem oficial pode continuar apenas em ambiente local/laboratorio, documentado como P1 em `docs/SECURITY.md`, ate existir tag oficial corrigida.
* O banco nunca deve ser exposto publicamente.

Build limpo recomendado apos mudancas de imagem/dependencia:

```powershell
cd "C:\Users\Famili Azevedo\Desktop\it-center-security-cloud"
docker compose -f infra/docker-compose.yml build --no-cache backend frontend
docker compose -f infra/docker-compose.yml up -d
```
