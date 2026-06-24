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
