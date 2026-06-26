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

# Sistema Operacional

Ubuntu Server LTS

Versão:

Sempre utilizar versão LTS.

---

# Estrutura

Internet
↓
Nginx
↓
Frontend Next.js
↓
Backend FastAPI
↓
PostgreSQL

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
