# Historico de Implantacao

Este documento registra o processo real de implantacao do IT Center Security Cloud na Oracle Cloud.

## 2026-07-28 - Recuperacao de acesso, criacao do primeiro admin e correcao do loop de login

Contexto: perda da chave SSH pessoal de acesso a `itcenter-edge-01`, ausencia de qualquer usuario administrativo na tabela `users` de producao, e um loop de login causado por conflito entre Basic Auth e Bearer token. Detalhes completos de cada causa raiz em `docs/deployment/POSTMORTEMS.md` (INCIDENTE 018, 019 e 020).

Linha do tempo:

1. Acesso SSH recuperado via workflow temporario `ssh-access-recovery.yml` (commit `b121ead`), que reaproveitou o secret `PROD_SSH_PRIVATE_KEY` ja usado pelo deploy para injetar uma nova chave publica no `authorized_keys` da VM.
2. Uma chave privada foi exposta acidentalmente durante o processo; foi tratada como comprometida e removida do `authorized_keys` assim que uma chave limpa ficou disponivel.
3. Workflow temporario removido do repositorio apos uso (commit `cdd85e2`).
4. Senha do HTTP Basic Auth (`admin`, `.secrets/dashboard.htpasswd`) redefinida via `htpasswd`.
5. Identificado que a tabela `users` estava vazia em producao. Primeiro usuario administrativo criado executando `backend/create_admin.py` manualmente dentro do container (o script nao faz parte da imagem Docker do backend).
6. Diagnosticado loop de login: chamadas autenticadas do dashboard (`Authorization: Bearer ...`) colidiam com o `Authorization: Basic` exigido pelo Nginx em `location /`.
7. Corrigido isentando `/api/backend/` do Basic Auth no Nginx (commit `c95586c`, ver ADR-023), aplicado na VM via `git pull` + `docker compose restart nginx`.
8. Login administrativo validado com sucesso no navegador, dashboard operacional (`/security` exibindo eventos reais).

Resultado:

* Acesso SSH administrativo restaurado com chave nova, sem chaves comprometidas remanescentes no `authorized_keys`.
* Primeiro usuario `admin` ativo criado em producao (`daniel.azevedo081205@gmail.com`).
* Login administrativo e navegacao no dashboard funcionando de ponta a ponta em producao.

## 2026-07-28 - Validacao de TLS, rollback e restore (fechamento da EPIC 13)

Contexto: ultimos tres itens pendentes da EPIC 13 validados em sequencia, do menor para o maior risco.

1. **TLS**: `TLS_RENEW_DRY_RUN=1 sh infra/scripts/renew-tls.sh` concluiu "all simulated renewals succeeded". Durante essa validacao foi descoberta a tag inexistente `certbot/certbot:v4.21.0` (INCIDENTE 021), corrigida para `v5.7.0` (commit `c682c7e`). Apos a correcao, a renovacao real (`sh infra/scripts/renew-tls.sh`) confirmou corretamente que o certificado so expira em 2026-09-24 e nao tentou renovar.
2. **Rollback**: backup gerado, `sh infra/scripts/rollback.sh f27d00c` executado com sucesso (containers reconstruidos e saudaveis, `postgres_data` preservado sem reiniciar o Postgres), seguido de `sh infra/scripts/rollback.sh c682c7e` para retornar ao estado atual. Dashboard validado funcional apos o rollforward.
3. **Restore**: backup fresco gerado (`itcenter-postgres-20260728T180730Z.sql.gz`) e restaurado com `ITCENTER_RESTORE_CONFIRM=YES sh infra/scripts/restore.sh` contra o proprio banco de producao. Schema recriado do zero, todas as tabelas restauradas com contagens consistentes com o backup, `/api/v1/health` respondendo `healthy` e dashboard funcional apos o restore.

Resultado: os tres itens `[~]` da EPIC 13 (`Testar restore em ambiente controlado`, `Validar rollback de deploy`, `Validar renovacao de certificado TLS`) ficam `[x]` em `docs/development/TASKS.md`. EPIC 13 considerada concluida, restando apenas a atualizacao continua de `POSTMORTEMS.md` quando houver incidente futuro.

## 2026-06-30 - Deploy manual via GitHub Actions

Workflow:

```text
Deploy Production
```

Commit implantado:

```text
7f5f846d4b51f9293daee8c943a05288e6976901
```

Resultado:

* `git fetch` autenticado via GitHub Actions concluido com sucesso.
* Backup PostgreSQL criado antes do deploy: `itcenter-postgres-20260630T231819Z.sql.gz`.
* Preflight de producao aprovado: Docker, Docker Compose, disco, memoria, secrets, dominio, TLS, rede, portas e volumes.
* Build das imagens `infra-backend` e `infra-frontend` concluido.
* Containers recriados e saudaveis: `itcenter-postgres`, `itcenter-backend`, `itcenter-frontend` e `itcenter-nginx`.
* Smoke tests de producao aprovados.
* Dashboard validado no navegador sem bug visual reportado.

URLs validadas:

```text
Dashboard: https://itcenter-daniel.chickenkiller.com/
Agent check-in: https://itcenter-daniel.chickenkiller.com/api/v1/agent/checkin
```

## 2026-06-30 - Validacao do ciclo periodico do agente

Resultado:

* Agente Windows permaneceu integrado ao ambiente publicado.
* Maquinas continuaram aparecendo no dashboard apos a validacao inicial.
* Ciclo periodico de check-in considerado validado operacionalmente.

Evidencia funcional:

```text
Dashboard publicado mantendo maquinas visiveis:
https://itcenter-daniel.chickenkiller.com/machines
```

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

Foi identificado que o Next.js standalone respondia corretamente pelo DNS interno Docker, mas recusava conexao quando o smoke test consultava `127.0.0.1:3000` em determinado contexto de container.

O smoke test e o healthcheck de producao foram ajustados para validar o frontend pela rede Docker.

Resultado:

```text
nginx -> http://frontend:3000/ -> 200 OK
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
* Permissao `600` em `dashboard.htpasswd` gerou `500 Internal Server Error` no Nginx; corrigido para `644`.
* Pouca memoria na VM exigiu criacao de Swap.
* O preflight precisou ser executado com `MIN_MEM_MB=256` apos confirmacao de swap ativo na Oracle Free Tier.
* O agente Windows retornou `401` enquanto usava API key diferente de `AGENT_API_KEY` em producao; corrigido ao alinhar a chave instalada no agente.

### 14. Estado final

```text
Infraestrutura: funcional
HTTPS: funcional
Nginx: funcional
Dashboard: funcional
Backend: funcional
PostgreSQL: funcional
Windows Agent: integrado e enviando check-in com 200 OK
```
