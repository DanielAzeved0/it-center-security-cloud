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

### Auditoria de segurança do frontend (2026-07-29)

Revisão completa de `frontend/dashboard/` (nenhuma chave de banco ou de backend encontrada no código ou em `.env` versionado). Achados e prioridade de risco, rastreados na EPIC 17 de `docs/development/TASKS.md`:

Prioridade Alta:

* Token de autenticação guardado em `localStorage` em vez de cookie `httpOnly` — detalhado em `docs/security/AUTH.md`.
* Ausência de security headers (`Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`) configurados no próprio Next.js (`next.config.mjs`). Não confirmado se o Nginx já cobre esses headers para o dashboard; se não cobrir, é a única linha de defesa contra clickjacking/MIME sniffing.

Prioridade Média:

* `app/api/backend/[...path]/route.ts` aceita fallback para `NEXT_PUBLIC_API_BASE_URL`. Hoje só é lido no route handler (server-only, não vaza para o bundle client), mas o prefixo `NEXT_PUBLIC_` sinaliza uso client-side e pode vazar a URL do backend no bundle público se reaproveitado futuramente em um client component.
* Não existe `middleware.ts`; a checagem de sessão acontece só dentro do componente `Shell` no client, sem gate no edge.
* `npm audit` no frontend não pôde ser validado no ambiente atual de desenvolvimento (proxy corporativo bloqueia o registry com certificado self-signed); falta rotina alternativa de auditoria de dependências do frontend.

Prioridade Baixa:

* `.dockerignore` do frontend não exclui `.env*`; não há vazamento hoje (nenhum `.env` existe no repositório), mas é uma prevenção ausente contra embutir `NEXT_PUBLIC_*` de um `.env` local no build da imagem.
* O proxy `/api/backend/[...path]` repassa qualquer path para o backend sem allowlist explícita de rotas.
* Mensagens de erro do backend (`detail`) são exibidas diretamente na UI sem filtragem adicional do frontend.

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
