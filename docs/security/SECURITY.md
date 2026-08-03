# SECURITY.md

# Política de Segurança

## Objetivo

Garantir que o IT Center Security Cloud seja desenvolvido seguindo princípios de segurança desde o início.

---

# Princípios

## Menor Privilégio

Cada componente deve possuir apenas as permissões necessárias.

---

## Criptografia

Todo tráfego externo deve utilizar HTTPS.

---

## Segredos

Nunca armazenar:

* Senhas
* Tokens
* Chaves

Dentro do código-fonte.

Utilizar:

.env

---

## Auditoria

Toda ação crítica deverá gerar logs.

---

## Proteção da API

Implementado:

* API Key obrigatória para agentes (`X-Agent-Api-Key`)
* Validação de payloads
* Erros sem detalhes internos
* Login administrativo com Bearer token assinado por HMAC SHA-256 (ADR-022, não JWT)
* RBAC (`admin`/`analyst`/`viewer`)
* Logs de auditoria (login, falha de login, logout, resolução de alerta)

Futuro:

* Rate limit

---

## Proteção do Banco

* Acesso apenas interno
* Sem exposição pública
* Backups automáticos

---

## Segurança do Agente

* Comunicação HTTPS
* API Key obrigatória
* Header oficial: X-Agent-Api-Key
* Validação de payload
* Cache offline sem dados sensíveis

---

## Segurança do Dashboard

Duas camadas, desde a EPIC 12 (ADR-021, ADR-022):

* Login administrativo da aplicação: Bearer token HMAC SHA-256, senha em PBKDF2-SHA256, papéis `admin`/`analyst`/`viewer` — contrato completo em `docs/security/AUTH.md`.
* O Nginx ainda exige HTTP Basic Auth como camada extra de borda para as páginas e assets estáticos (`.secrets/dashboard.htpasswd`, fora do Git, montado somente em leitura) — isso não substitui o login da aplicação (ADR-023).
* O endpoint público do agente é limitado a `POST /api/v1/agent/checkin`; ele não recebe Basic Auth porque valida obrigatoriamente `X-Agent-Api-Key` no FastAPI.
* Endpoints internos do backend não são expostos em portas públicas.

Limitação conhecida:

* O Basic Auth do Nginx é redundante agora que o login administrativo completo está em produção; sua real necessidade deve ser reavaliada (ver ADR-023).

### Auditoria de segurança do frontend (2026-07-29) — corrigida na EPIC 17

Revisão completa de `frontend/dashboard/` (nenhuma chave de banco ou de backend encontrada no código ou em `.env` versionado). Todos os achados abaixo (`docs/development/TASKS.md`, EPIC 17) foram corrigidos:

* Token de autenticação migrado de `localStorage` para cookie `itcenter_session` (`httpOnly` + `Secure` condicional a HTTPS real + `SameSite=Strict`), setado pelo proxy `/api/backend` no login — detalhado em `docs/security/AUTH.md`.
* `Content-Security-Policy` adicionada em `next.config.mjs`. `X-Frame-Options`, `X-Content-Type-Options` e `Referrer-Policy` **não** foram duplicados no Next.js: o Nginx já os aplica globalmente em produção (`infra/nginx/nginx.conf.template`) — duplicar geraria o mesmo header duas vezes sem ganho real.
* Removido o fallback `NEXT_PUBLIC_API_BASE_URL` do proxy; só `ITCENTER_API_BASE_URL` é aceito (sempre definido tanto local quanto em produção).
* Criado `middleware.ts`: bloqueia `/`, `/machines`, `/alerts` e `/security` sem o cookie de sessão presente, redirecionando para `/login` no edge. A validade do token continua sendo checada em `/api/v1/auth/me` (`Shell.tsx`) — o middleware só verifica presença do cookie, não sua validade.
* `npm audit --audit-level=high` roda no job `frontend` do CI (`.github/workflows/ci.yml`), com acesso direto ao registry (sem o proxy corporativo que bloqueia o comando localmente); registrado em `docs/deployment/WEEKLY_OPERATIONS.md`.
* `.dockerignore` do frontend agora exclui `.env`, `.env.local` e `.env*.local`.
* O proxy `/api/backend/[...path]` agora valida uma allowlist explícita de prefixos (`api/v1/health`, `api/v1/auth/*`, `api/v1/machines*`, `api/v1/alerts*`, `api/v1/security-events`) e responde 404 para qualquer outro path.
* Confirmado (revisão de todo `backend/app/routes/*.py`): nenhum `HTTPException(detail=...)` interpola exceção ou erro interno — são strings estáticas genéricas ("Invalid credentials", "Machine not found" etc.) e não há handler genérico expondo stack trace. Não há vazamento de detalhes internos via `detail`.

---

# Requisitos Obrigatórios

Não serão aceitos:

* Senhas em texto plano
* Secrets no GitHub
* Banco exposto na internet
* HTTP sem TLS
* Check-in de agente sem API Key

---

# Varredura de Imagens e Dependencias

## Objetivo

Evitar que imagens Docker com vulnerabilidades criticas ou altas sejam promovidas para ambiente publicado.

## Ferramenta Padrao

Docker Scout.

Comandos obrigatorios antes de publicar uma nova imagem:

```powershell
docker scout cves postgres:16-alpine --only-severity critical,high
docker scout cves infra-backend:latest --only-severity critical,high
docker scout cves infra-frontend:latest --only-severity critical,high
```

Para investigar caminho de correcao:

```powershell
docker scout recommendations postgres:16-alpine
docker scout recommendations infra-backend:latest
docker scout recommendations infra-frontend:latest
```

## Prioridade

P0:

* Vulnerabilidade critica ou alta com pacote usado em runtime pelo backend ou frontend.
* Vulnerabilidade com exploracao remota sem autenticacao.
* Vulnerabilidade em componente exposto externamente.

P1:

* Vulnerabilidade critica ou alta em imagem oficial sem versao corrigida disponivel.
* Vulnerabilidade em pacote empacotado por framework quando nao existe versao upstream corrigida.
* Vulnerabilidade em dependencia indireta sem impacto claro no fluxo atual.

P2:

* Vulnerabilidades medias ou baixas.
* Alertas em ferramentas de desenvolvimento que nao entram na imagem final.

## Politica de Correcao

* Atualizar dependencias diretas para versoes corrigidas.
* Atualizar imagem base quando a recomendacao reduzir CVEs sem quebrar runtime.
* Nao usar `npm audit fix --force` sem revisao, porque pode trocar major versions e quebrar o dashboard.
* Nao ignorar vulnerabilidade critica ou alta sem registrar motivo em `docs/development/DECISIONS.md`.

## Estado Atual das Imagens

Backend:

* Base alterada para `python:3.13-alpine`.
* Resultado esperado no Docker Scout: zero vulnerabilidades critical/high.

Frontend:

* Next.js atualizado para `16.2.9`.
* `picomatch` fixado em `4.0.4`.
* O build executa `scripts/security/patch-next-picomatch.js` para substituir o `picomatch` compilado dentro do Next por `4.0.4`.
* A imagem final remove o `npm` global do runtime para evitar dependencias internas nao usadas, incluindo `picomatch` vulneravel empacotado pelo npm da imagem base.

PostgreSQL:

* Imagem oficial mantida em `postgres:16-alpine`.
* Se o Scout ainda apontar CVE em `golang/stdlib`, tratar como risco residual P1 enquanto nao houver tag oficial corrigida.
* O banco deve continuar sem exposicao externa e acessivel apenas pela rede Docker/host local controlado.
