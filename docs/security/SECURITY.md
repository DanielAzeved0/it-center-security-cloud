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
* Cache offline (`cache\checkin-*.json`, gravado por `Save-AgentOfflinePayload` quando o check-in falha) contém o payload completo do check-in — incluindo `local_admins`, status de firewall/Defender/RDP, IP/MAC/número de série e o inventário completo de programas instalados. **Corrigido na EPIC 28 (2026-08-17)**: a função de ACL do hardening da EPIC 16 (antes `Protect-AgentConfigFile`, restrita a `config.json`) foi generalizada para `Protect-AgentPath` (`agent-windows/install-agent.ps1`) e agora também é aplicada a `logs\` e `cache\` na instalação, restringindo os dois diretórios a SYSTEM/Administrators (`FullControl`) e removendo as regras de acesso herdadas anteriormente (leitura para `Users` via ACL padrão de `Program Files`). Como `logs\` e `cache\` são diretórios, a ACL é criada com `InheritanceFlags = ContainerInherit, ObjectInherit`, garantindo que arquivos gravados depois da instalação — como `cache\checkin-*.json`, criado em runtime pelo agente — herdem a mesma restrição em vez de cair de volta na ACL padrão do diretório pai.
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
* O proxy `/api/backend/[...path]` agora valida uma allowlist explícita de prefixos (`api/v1/health`, `api/v1/auth/login`, `api/v1/auth/me`, `api/v1/auth/logout`, `api/v1/machines`, `api/v1/alerts`, `api/v1/security-events`, `api/v1/dashboard`, `api/v1/reports` — os dois últimos adicionados na EPIC 20 para a tela executiva e a exportação de PDF) e responde 404 para qualquer outro path.
* Confirmado (revisão de todo `backend/app/routes/*.py`): nenhum `HTTPException(detail=...)` interpola exceção ou erro interno — são strings estáticas genéricas ("Invalid credentials", "Machine not found" etc.) e não há handler genérico expondo stack trace. Não há vazamento de detalhes internos via `detail`.

---

## OWASP Top 10 — Controles Reais Aplicados

Mapeamento concreto para os riscos mais relevantes deste projeto (API FastAPI + PostgreSQL + dashboard Next.js) — não é uma lista genérica, cada item cita o controle real existente no código:

* **Injection (SQL)**: o backend usa `psycopg` puro, sem ORM. Todas as queries em `backend/app/repositories/*.py` (`machines.py`, `alerts.py`, `audit_logs.py`, `local_admins.py`, `security_events.py`, `users.py`, `dashboard.py`) e em `backend/create_admin.py` usam parâmetros `%s` passados para `connection.execute(query, params)` — nenhuma ocorrência de concatenação ou f-string de valor de entrada dentro da string SQL foi encontrada no código atual.
* **Cross-Site Scripting (XSS)**: o frontend não usa `dangerouslySetInnerHTML`, `eval` nem HTML não sanitizado em nenhum componente (revisão completa em 2026-07-29, ver `## Segurança do Dashboard` acima). `Content-Security-Policy` está ativa (`next.config.mjs`), mas `script-src` inclui `'unsafe-inline'` — ou seja, a CSP **não bloqueia** a execução de um `<script>` injetado se surgir um vetor de XSS no futuro; ela não deve ser lida como mitigação de XSS enquanto essa diretiva estiver presente. **Investigado na EPIC 28 (2026-08-17): tentativa de remoção feita e revertida, risco avaliado e mantido como aceito** — não é mais "não avaliado". Confirmado que nenhum código próprio do projeto usa script inline, mas o próprio App Router do Next.js injeta scripts inline sem nonce (`self.__next_f.push(...)`, payload de streaming/hidratação de React Server Components) em toda página; removê-lo sem uma CSP baseada em nonce bloqueia esses scripts no browser e quebra a hidratação da aplicação inteira (comentário detalhado em `frontend/dashboard/next.config.mjs`). A correção real exigiria migrar a CSP para `middleware.ts` com nonce gerado por request — mudança arquitetural maior que uma correção pontual, precisa de planejamento próprio (ADR/EPIC dedicada) antes de ser implementada. O que continua protegido de forma independente da CSP é o token de sessão: ele fica em cookie `httpOnly`, então mesmo um script injetado que rodasse livremente não conseguiria ler o token via `document.cookie`. A CSP também mantém `style-src 'self' 'unsafe-inline'`; uma varredura do código atual de `frontend/dashboard` não encontrou nenhum componente usando o atributo `style` inline (prop `style={{...}}`) ou `<style>` embutido — diferente do `script-src`, esse `unsafe-inline` parece um resquício sem uso funcional conhecido hoje, não uma necessidade confirmada, mas ainda reduz a superfície de proteção da CSP.
* **Server-Side Request Forgery (SSRF)**: o backend não faz chamada de rede de saída para URL fornecida por payload externo (agente ou usuário) — não existe cliente HTTP outbound configurável por entrada de request. A integração com RustDesk (EPIC 19, ADR-027) só armazena o identificador `machines.rustdesk_id`; quem abre a conexão remota é o cliente RustDesk já instalado na máquina do operador, não o backend.
* **Path Traversal**: nenhum endpoint aceita caminho de arquivo como entrada do usuário para leitura em disco no backend. **Corrigido na EPIC 28 (2026-08-17) em duas camadas independentes.** Camada 1 (proxy): o Next.js já roda `decodeURIComponent()` em cada segmento do catch-all `[...path]` antes do handler ver o valor, então um segmento único como `api/v1/machines%2f..%2f..%2f..%2fdocs` chegava como um elemento de array contendo `/` e `..` literais — passava na checagem de allowlist (que só olhava o prefixo) e só era normalizado depois, por `new URL()`, resultando em `/docs` no backend. `toSafeSegments()` (`frontend/dashboard/app/api/backend/[...path]/route.ts`) agora re-separa cada segmento já decodificado pelos separadores reais (`/` e `\` — o parser WHATWG usado por `new URL()` trata `\` como `/` para esquemas especiais, então uma variante `%5c` teria o mesmo efeito) e rejeita com `404` qualquer componente vazio, `.` ou `..`, **antes** da checagem de allowlist. Camada 2 (backend, defesa em profundidade): `backend/app/main.py` desativa `docs_url`/`redoc_url`/`openapi_url` quando `APP_ENV=production`, então mesmo um bypass futuro no proxy não alcançaria o Swagger/OpenAPI da API interna em produção. Validado com `curl` contra `%2f`, `%5c`, `..` literal e `%2e%2e` — todos retornam `404`.
* **Quebra de Controle de Acesso**: RBAC (`admin`/`analyst`/`viewer`) é decidido no backend via `require_roles()` (`backend/app/services/auth.py`), não apenas escondido no frontend — botões desabilitados no dashboard para `viewer` são só reforço de UX, a aplicação real da regra é sempre no servidor. Os dois mecanismos de autenticação não se misturam: `X-Agent-Api-Key` nunca concede papel de usuário humano, e Bearer token humano não é aceito no check-in do agente.

Riscos conhecidos e aceitos relacionados a este tópico (detalhados também em `docs/security/AUTH.md`):

* `POST /api/v1/auth/login` não tem rate limit nem lockout de conta hoje — nem no Nginx (só existe `limit_req_zone` para a zona `agent_checkins`, `infra/nginx/nginx.conf.template`) nem na aplicação. Mitigação parcial já existente: mensagem de erro genérica (não confirma se o e-mail existe) e log de auditoria (`auth.login_failed`) a cada tentativa. **Corrigido na EPIC 28 (2026-08-17)**: antes, essa mensagem genérica não fechava completamente a enumeração de contas, porque o código fazia curto-circuito (`user is None or status != "active" or not verify_password(...)`) e só rodava o PBKDF2 de 210.000 iterações — lento por natureza — quando o usuário existia e estava ativo; a diferença de tempo de resposta entre um e-mail existente e um inexistente permitia enumerar contas por timing attack mesmo com a mensagem idêntica. `backend/app/routes/auth.py` agora sempre roda `verify_password` — contra o hash real do usuário quando o e-mail existe (independentemente do status) ou contra um hash dummy pré-computado no módulo (`_DUMMY_PASSWORD_HASH`, calculado uma única vez na importação, não a cada request) quando não existe — antes de decidir se a requisição falha, equalizando o tempo de resposta entre os dois casos. Uma correção efetiva de rate limit/lockout continua exigindo planejamento e ADR formal antes de implementação, conforme `docs/development/CONTRIBUTING.md` — não é tratada como pendência com prazo, e sim como risco aceito enquanto o MVP roda em escala pequena.
* O hash de senha usa PBKDF2-HMAC-SHA256 com `PASSWORD_ITERATIONS = 210_000` (`backend/app/services/auth.py`), abaixo da recomendação atual da OWASP para esse algoritmo (600.000+ iterações). Isso reduz a margem de segurança em caso de vazamento do banco (quebra offline do hash fica mais barata), mas não é, isoladamente, uma vulnerabilidade explorável sem esse vazamento adicional. Registrado como risco aceito/conhecido, sem mudança de valor planejada nesta etapa.
* Personificação de máquina via `AGENT_API_KEY` compartilhada — **corrigido na EPIC 28-A (2026-08-17, ADR-036)**: até então, o backend validava apenas a chave global e identificava a máquina só pelo `hostname` autorreportado, sem vínculo servidor-side entre a chave usada e uma máquina específica, permitindo forjar check-in em nome de qualquer outro hostname já cadastrado. Agora existe um segredo por máquina em modelo trust-on-first-use (`machines.agent_secret_hash`): o primeiro check-in de cada hostname adota um segredo aleatório de 256 bits, devolvido em texto puro só nessa resposta; check-ins seguintes precisam enviá-lo de volta, e uma divergência é rejeitada (401, sem sobrescrever dado nenhum) e gera o evento/alerta `machine_identity_mismatch` (severidade alta). Detalhado em `docs/security/AUTH.md` (seção "API Key por Agente").

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

`infra/scripts/docker-scout-gate.sh` deixou de ser apenas documentado como obrigatorio: desde a EPIC 29 (2026-08-17), `infra/scripts/deploy.sh` o invoca automaticamente entre o `build` e o `up -d` de todo deploy de producao. Como o script roda com `set -eu`, uma falha do gate (CVE `critical`/`high` em qualquer imagem de `ITCENTER_SCOUT_IMAGES`) aborta o deploy antes de qualquer container novo subir, sem depender de um humano lembrar de rodar manualmente.

Comandos obrigatorios antes de publicar uma nova imagem (equivalente ao que o gate automatizado roda, util para investigacao pontual):

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
* `postcss`, `sharp` e `nanoid` fixados via `overrides` em `package.json` (`8.5.25`, `0.35.3` e `3.3.18` respectivamente) porque `next@16.2.12` ainda declara essas dependencias internas em versoes vulneraveis (XSS/path traversal no PostCSS, CVEs de libvips no sharp, previsibilidade de ID em `nanoid` — `GHSA-2v37-7h3g-55p8`) — mesmo padrao do fix de `picomatch` abaixo, aplicado via `npm overrides` em vez de patch de arquivo porque sao dependencias normais, nao codigo vendorizado.
* `picomatch` fixado em `4.0.4`.
* O build executa `scripts/security/patch-next-picomatch.js` para substituir o `picomatch` compilado dentro do Next por `4.0.4`.
* A imagem final remove o `npm` global do runtime para evitar dependencias internas nao usadas, incluindo `picomatch` vulneravel empacotado pelo npm da imagem base.

PostgreSQL:

* Imagem oficial mantida em `postgres:16-alpine`.
* Se o Scout ainda apontar CVE em `golang/stdlib`, tratar como risco residual P1 enquanto nao houver tag oficial corrigida.
* O banco deve continuar sem exposicao externa e acessivel apenas pela rede Docker/host local controlado.
