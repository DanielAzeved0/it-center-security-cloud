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
* Rate limit no check-in do agente (Nginx, `limit_req` na zona `agent_checkins`, `infra/nginx/nginx.conf.template`), validado em produção

Futuro:

* Rate limit geral nas demais rotas da API (hoje só o check-in do agente tem limite aplicado)

---

## RustDesk (EPIC 19, ADR-027)

`machines.rustdesk_id` é apenas um identificador armazenado (não uma credencial) e o backend não faz nenhuma chamada de rede externa para o RustDesk — o botão "Conectar" apenas abre o cliente já instalado na máquina do operador.

A integração com Snipe-IT (ADR-028) foi implementada junto com o RustDesk na EPIC 19, mas foi **revertida em 2026-08-11** (ver ADR-033 em `docs/development/DECISIONS.md`): nunca existiu um Snipe-IT real conectado em produção, sem necessidade concreta de ITAM identificada. Código, secrets e a coluna `machines.snipeit_asset_id` foram removidos.

---

## Observabilidade de Infraestrutura (EPIC 21, ADR-030)

`node_exporter`, `cadvisor`, `prometheus` e `grafana` (`infra/docker-compose.production.yml`, sob `profiles: ["observability"]`) monitoram o Edge Node e os containers Docker — nunca as máquinas Windows monitoradas pelo agente (essas continuam isoladas em `metrics`, EPIC 3).

* **Nunca expostos publicamente**: nenhum dos quatro publica porta no host (`ports:` ausente no Compose) nem tem `location` própria em `infra/nginx/nginx.conf.template`. Nginx continua o único ponto de entrada público do Edge Node.
* **Acesso operacional**: apenas via `docker exec` nos containers ou túnel SSH direto ao IP do container na rede Docker interna `itcenter-network` (procedimento em `docs/architecture/NETWORK.md`) — nunca por rota autenticada adicional no Nginx, a menos que uma decisão futura formalize isso com Basic Auth equivalente.
* **Menor privilégio**: `cadvisor` roda deliberadamente sem `privileged: true`, aceitando perder algumas métricas de I/O em disco em troca de não conceder acesso privilegiado ao host — decisão registrada em `docs/architecture/CONTAINERS.md`.
* **Sem acesso ao `docker.sock`**: revisão de segurança de 2026-08-15 removeu o mount `/var/run:/var/run:ro` do `cadvisor` — um mount `:ro` do diretório não impede chamadas sobre o socket do Docker já existente ali, então um RCE no cAdvisor poderia usar a API do Docker para criar um container privilegiado e obter root no host, apesar de `privileged: true` já estar desligado. Sem esse mount, o `cadvisor` perde enriquecimento de nome/labels do container (mostra ID/caminho de cgroup), mas mantém CPU/memória/IO por container via `/sys` e `/var/lib/docker`.
* **Risco residual aceito: mounts de `/` inteiro em `node_exporter` (`/:/host/root:ro`) e `cadvisor` (`/:/rootfs:ro`)**: é o padrão oficial documentado dessas duas ferramentas para calcular uso de disco corretamente a partir da perspectiva do host, mas dá a esses dois containers acesso de leitura a todo o filesystem — incluindo `.env.production` (segredos de produção) e as chaves privadas do Let's Encrypt em `/etc/letsencrypt`. Uma RCE nessas imagens (ou um comprometimento de supply chain) exfiltraria esses segredos sem precisar de `privileged: true` nem do `docker.sock`. Mitigação: imagens com tag fixa cobertas pelo gate de CVE do Docker Scout (`infra/scripts/docker-scout-gate.sh`, `ITCENTER_SCOUT_IMAGES`) antes de cada build; sem isolamento adicional além disso no MVP atual — reavaliar se a superfície de ataque crescer (mais serviços expostos na mesma rede, por exemplo).
* **Credencial do Grafana**: `GF_SECURITY_ADMIN_PASSWORD` vem de `GRAFANA_ADMIN_PASSWORD` em `.env.production`. Sem esse valor definido, o Compose usa um fallback deliberadamente óbvio (`changeme-configure-GRAFANA_ADMIN_PASSWORD-before-observability`) em vez de falhar — usar `:?` (variável obrigatória) quebraria `docker compose config`/`up` mesmo para quem nunca ativa o profile `observability`, já que o Compose interpola variáveis de todos os serviços do arquivo independentemente do profile ativo. `infra/scripts/ops-check.sh` falha (`FAIL`) se o container `itcenter-grafana` estiver rodando com esse fallback ainda ativo. Defina `GRAFANA_ADMIN_PASSWORD` com um valor forte antes de ativar `--profile observability`; nunca deixe o fallback em produção nem use a senha padrão `admin`/`admin` do Grafana.
* **Ativação opt-in por causa da RAM**: a VM é Oracle Free Tier de 1GB (`itcenter-edge-01`), já rodando justa com os 4 serviços atuais (ver `MEM_WARN_MB`/`MEM_FAIL_MB` em `infra/scripts/ops-check.sh`). Os 4 novos serviços têm `mem_limit` conservador cada (node_exporter ~30M, cadvisor ~100M, prometheus ~200M, grafana ~150M) e retenção curta no Prometheus (5 dias / 200MB), mas a soma ainda exige validação manual de memória/disco disponíveis antes de qualquer ativação real em produção — não simulada, ver `docs/development/TASKS.md`.
* **Rede plana**: os 4 serviços novos compartilham a mesma rede Docker `itcenter-network` do `postgres`/`backend`, sem segmentação adicional — não é uma regressão desta EPIC (os serviços existentes já dividiam essa rede), mas amplia a superfície dentro dela. Sem ação nesta rodada; candidato a uma segunda rede Compose dedicada se a superfície de observabilidade crescer.

---

## Proteção do Banco

* Acesso apenas interno
* Sem exposição pública
* Backups automáticos

Ver detalhes de rede/volume/caminho de backup em `docs/architecture/SECURITY.md`.

---

## Segurança do Agente

* Comunicação HTTPS
* API Key obrigatória
* Header oficial: X-Agent-Api-Key
* Validação de payload
* Cache offline sem dados sensíveis
* Hardening da EPIC 16 concluído: scripts do agente assinados com certificado Authenticode self-signed e Tarefa Agendada executando com `ExecutionPolicy AllSigned` (ADR-025/ADR-031, commit `969201b`)

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
* Criado `middleware.ts`: bloqueia `/`, `/machines`, `/alerts`, `/security` e `/executive` (rota adicionada ao `matcher` na EPIC 26, estava faltando) sem o cookie de sessão presente, redirecionando para `/login` no edge. A validade do token continua sendo checada em `/api/v1/auth/me`, via `AuthProvider` (`components/AuthProvider.tsx`, buscado uma única vez por sessão no layout `app/(authenticated)/layout.tsx` desde a EPIC 26) — o middleware só verifica presença do cookie, não sua validade.
* `npm audit --audit-level=high` roda no job `frontend` do CI (`.github/workflows/ci.yml`), com acesso direto ao registry (sem o proxy corporativo que bloqueia o comando localmente); registrado em `docs/deployment/WEEKLY_OPERATIONS.md`.
* `.dockerignore` do frontend agora exclui `.env`, `.env.local` e `.env*.local`.
* O proxy `/api/backend/[...path]` agora valida uma allowlist explícita de prefixos (`api/v1/health`, `api/v1/auth/*`, `api/v1/machines*`, `api/v1/alerts*`, `api/v1/security-events`) e responde 404 para qualquer outro path.
* Confirmado (revisão de todo `backend/app/routes/*.py`): nenhum `HTTPException(detail=...)` interpola exceção ou erro interno — são strings estáticas genéricas ("Invalid credentials", "Machine not found" etc.) e não há handler genérico expondo stack trace. Não há vazamento de detalhes internos via `detail`.

---

## OWASP Top 10 — Controles Reais Aplicados

Mapeamento concreto para os riscos mais relevantes deste projeto (API FastAPI + PostgreSQL + dashboard Next.js) — não é uma lista genérica, cada item cita o controle real existente no código:

* **Injection (SQL)**: o backend usa `psycopg` puro, sem ORM. Todas as queries em `backend/app/repositories/*.py` (`machines.py`, `alerts.py`, `audit_logs.py`, `local_admins.py`, `security_events.py`, `users.py`, `dashboard.py`) e em `backend/create_admin.py` usam parâmetros `%s` passados para `connection.execute(query, params)` — nenhuma ocorrência de concatenação ou f-string de valor de entrada dentro da string SQL foi encontrada no código atual.
* **Cross-Site Scripting (XSS)**: o frontend não usa `dangerouslySetInnerHTML`, `eval` nem HTML não sanitizado em nenhum componente (revisão completa em 2026-07-29, ver `## Segurança do Dashboard` acima). `Content-Security-Policy` está ativa (`next.config.mjs`) e o token de sessão fica em cookie `httpOnly` — mesmo que surgisse um XSS, o token não seria lido por JavaScript.
* **Server-Side Request Forgery (SSRF)**: o backend não faz chamada de rede de saída para URL fornecida por payload externo (agente ou usuário) — não existe cliente HTTP outbound configurável por entrada de request. A integração com RustDesk (EPIC 19, ADR-027) só armazena o identificador `machines.rustdesk_id`; quem abre a conexão remota é o cliente RustDesk já instalado na máquina do operador, não o backend.
* **Path Traversal**: nenhum endpoint aceita caminho de arquivo como entrada do usuário para leitura em disco. O proxy interno do dashboard (`frontend/dashboard/app/api/backend/[...path]/route.ts`) valida uma allowlist explícita de prefixos de rota antes de repassar ao backend e responde `404` para qualquer path fora dela — o `[...path]` dinâmico do Next.js não vira um encaminhador aberto para rotas arbitrárias.
* **Quebra de Controle de Acesso**: RBAC (`admin`/`analyst`/`viewer`) é decidido no backend via `require_roles()` (`backend/app/services/auth.py`), não apenas escondido no frontend — botões desabilitados no dashboard para `viewer` são só reforço de UX, a aplicação real da regra é sempre no servidor. Os dois mecanismos de autenticação não se misturam: `X-Agent-Api-Key` nunca concede papel de usuário humano, e Bearer token humano não é aceito no check-in do agente.

Riscos conhecidos e aceitos relacionados a este tópico (detalhados também em `docs/security/AUTH.md`):

* `POST /api/v1/auth/login` não tem rate limit nem lockout de conta hoje — nem no Nginx (só existe `limit_req_zone` para a zona `agent_checkins`, `infra/nginx/nginx.conf.template`) nem na aplicação. Mitigação parcial já existente: mensagem de erro genérica (não confirma se o e-mail existe) e log de auditoria (`auth.login_failed`) a cada tentativa. Uma correção efetiva (rate limit/lockout) exigiria planejamento e ADR formal antes de implementação, conforme `docs/development/CONTRIBUTING.md` — não é tratada como pendência com prazo, e sim como risco aceito enquanto o MVP roda em escala pequena.
* O hash de senha usa PBKDF2-HMAC-SHA256 com `PASSWORD_ITERATIONS = 210_000` (`backend/app/services/auth.py`), abaixo da recomendação atual da OWASP para esse algoritmo (600.000+ iterações). Isso reduz a margem de segurança em caso de vazamento do banco (quebra offline do hash fica mais barata), mas não é, isoladamente, uma vulnerabilidade explorável sem esse vazamento adicional. Registrado como risco aceito/conhecido, sem mudança de valor planejada nesta etapa.

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

* Next.js atualizado para `16.2.12` em 2026-08-03 (`npm audit --audit-level=high` no CI apontou 3 CVEs high em `next@16.2.9` — bypass de middleware/proxy, SSRF em rewrites e DoS em Server Actions; `16.2.12` corrige todas).
* `postcss` e `sharp` fixados via `overrides` em `package.json` (`8.5.25` e `0.35.3`) porque `next@16.2.12` ainda declara essas duas dependencias internas em versoes vulneraveis (XSS/path traversal no PostCSS, CVEs de libvips no sharp) — mesmo padrao do fix de `picomatch` abaixo, aplicado via `npm overrides` em vez de patch de arquivo porque sao dependencias normais, nao codigo vendorizado.
* `picomatch` fixado em `4.0.4`.
* O build executa `scripts/security/patch-next-picomatch.js` para substituir o `picomatch` compilado dentro do Next por `4.0.4`.
* A imagem final remove o `npm` global do runtime para evitar dependencias internas nao usadas, incluindo `picomatch` vulneravel empacotado pelo npm da imagem base.

PostgreSQL:

* Imagem oficial mantida em `postgres:16-alpine`.
* Se o Scout ainda apontar CVE em `golang/stdlib`, tratar como risco residual P1 enquanto nao houver tag oficial corrigida.
* O banco deve continuar sem exposicao externa e acessivel apenas pela rede Docker/host local controlado.
