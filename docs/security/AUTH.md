# Autenticacao

Este documento descreve os mecanismos de autenticacao atuais do IT Center Security Cloud.

## Objetivo

Substituir os controles minimos do MVP por autenticacao administrativa com usuarios humanos, papeis, permissoes e auditoria.

O desenho abaixo define o contrato implementado da EPIC 12 para login administrativo, RBAC e auditoria inicial.

## Fronteiras

Existem dois mecanismos separados:

```text
Agente Windows -> X-Agent-Api-Key
Usuario humano -> Login administrativo com Bearer token
```

Regras:

* `X-Agent-Api-Key` continua exclusivo para check-in do agente.
* Usuarios administrativos nao devem usar a API Key do agente.
* Rotas administrativas exigem Bearer token de usuario humano.
* A autenticacao administrativa nao deve alterar o contrato atual de check-in do agente.

## Dashboard

No MVP, o dashboard e protegido por HTTP Basic Auth no Nginx.

Arquivo:

```text
.secrets/dashboard.htpasswd
```

Esse arquivo nao deve ser commitado.

Criacao:

```bash
mkdir -p .secrets
docker run --rm httpd:2.4-alpine htpasswd -Bbn admin 'SENHA_FORTE_AQUI' > .secrets/dashboard.htpasswd
chmod 700 .secrets
chmod 644 .secrets/dashboard.htpasswd
```

O arquivo `dashboard.htpasswd` precisa ser legivel pelo worker do Nginx dentro do container. Por isso, em producao, use `644` no arquivo e mantenha a pasta `.secrets` com `700`.

## Agente Windows

O agente usa API Key no header:

```text
X-Agent-Api-Key
```

O valor vem de:

```text
AGENT_API_KEY
```

Esse valor fica em `.env.production` no servidor e nunca deve ser versionado.

## Modelo de Usuario

Tabela:

```text
users
```

Campos minimos:

| Campo | Tipo Conceitual | Obrigatorio | Observacao |
| --- | --- | --- | --- |
| `id` | integer/uuid | sim | Identificador interno. |
| `email` | string | sim | Unico, usado para login. |
| `name` | string | sim | Nome exibido no dashboard. |
| `password_hash` | string | sim | Hash forte, nunca senha em texto puro. |
| `role` | enum | sim | `admin`, `analyst` ou `viewer`. |
| `status` | enum | sim | `active`, `disabled` ou `pending`. |
| `created_at` | timestamp | sim | Criacao do usuario. |
| `updated_at` | timestamp | sim | Ultima alteracao. |
| `last_login_at` | timestamp nullable | nao | Ultimo login bem-sucedido. |

Invariantes:

* `email` deve ser unico.
* A unicidade de `email` e case-insensitive por indice unico em `lower(email)`.
* `password_hash` nunca deve ser retornado por API.
* Usuario `disabled` nao pode autenticar.
* Alteracao de `role` deve ser auditada.
* Criacao do primeiro `admin` deve ser controlada por seed/migration ou comando operacional documentado.

## Primeiro Admin

O primeiro usuario administrador pode ser criado por script operacional, sem senha padrao versionada.

Exemplo local:

```powershell
$env:ADMIN_EMAIL='admin@example.com'
$env:ADMIN_NAME='Admin'
$env:ADMIN_PASSWORD='SENHA_FORTE_AQUI'
python backend\create_admin.py
```

O script:

* cria apenas usuario `admin` ativo;
* armazena somente `password_hash`;
* nao altera usuario existente com o mesmo e-mail;
* exige `ADMIN_EMAIL` e `ADMIN_PASSWORD`.

## Papeis

### admin

Responsavel por administracao completa.

Permissoes:

* Visualizar dashboard, maquinas, metricas, programas, administradores locais, eventos e alertas.
* Resolver alertas.
* Gerenciar usuarios.
* Alterar configuracoes administrativas.
* Alterar politicas SOC quando essa funcao existir no produto.

### analyst

Responsavel por operacao diaria de seguranca.

Permissoes:

* Visualizar dashboard, maquinas, metricas, programas, administradores locais, eventos e alertas.
* Investigar e resolver alertas.
* Nao pode gerenciar usuarios.
* Nao pode alterar configuracoes administrativas globais.

### viewer

Responsavel por leitura operacional.

Permissoes:

* Visualizar dashboard, maquinas, metricas, programas, administradores locais, eventos e alertas.
* Nao pode resolver alertas.
* Nao pode gerenciar usuarios.
* Nao pode alterar configuracoes ou politicas.

## Matriz de Permissoes

| Recurso/Acao | admin | analyst | viewer |
| --- | --- | --- | --- |
| Visualizar dashboard | sim | sim | sim |
| Visualizar maquinas | sim | sim | sim |
| Visualizar metricas | sim | sim | sim |
| Visualizar programas instalados | sim | sim | sim |
| Visualizar administradores locais | sim | sim | sim |
| Visualizar eventos de seguranca | sim | sim | sim |
| Visualizar alertas | sim | sim | sim |
| Resolver alertas | sim | sim | nao |
| Cadastrar/editar RustDesk ID da maquina (EPIC 19) | sim | sim | nao |
| Conectar via RustDesk (botao no dashboard, EPIC 19) | sim | sim | nao |
| Visualizar Dashboard Executivo / exportar relatorios PDF (EPIC 20) | sim | sim | sim |
| Gerenciar usuarios | sim | nao | nao |
| Alterar configuracoes administrativas | sim | nao | nao |
| Alterar politica SOC | sim | nao | nao |

## Sessoes ou JWT

Decisao implementada:

```text
Usar Bearer token assinado por HMAC SHA-256 para usuario humano.
```

Configuracao:

```text
AUTH_TOKEN_SECRET
AUTH_TOKEN_EXPIRATION_MINUTES
```

Regras:

* Token expira pelo campo `exp`.
* Em producao, `AUTH_TOKEN_SECRET` deve ser configurado com valor nao padrao.
* Senha nao trafega ou e armazenada em texto puro.
* Senhas sao verificadas contra `password_hash` PBKDF2-SHA256.
* Rotas administrativas validam usuario ativo e permissao.
* Logout registra auditoria; o token expira naturalmente.
* Erros de login sao genericos para nao enumerar usuarios. Desde a EPIC 28 (2026-08-17), isso vale tambem para o tempo de resposta: `POST /api/v1/auth/login` (`backend/app/routes/auth.py`) sempre roda `verify_password` (PBKDF2, 210.000 iteracoes) — contra o hash real quando o e-mail existe (ativo ou nao) ou contra um hash dummy pre-computado no modulo quando nao existe — antes de decidir se a requisicao falha, eliminando a diferenca de latencia que antes distinguia conta cadastrada de inexistente.

### Fallback de desenvolvimento do `AUTH_TOKEN_SECRET`

O código (`backend/app/services/auth.py`) tem um fallback hardcoded, `DEFAULT_DEVELOPMENT_SECRET = "development-auth-secret-change-in-production"`, usado quando a variável de ambiente `AUTH_TOKEN_SECRET` não está definida. Isso existe para permitir rodar o backend localmente sem configurar `.env` na primeira vez.

A única proteção real contra esse fallback vazar para produção é a validação de startup `validate_runtime_configuration()` (`backend/app/core/config.py`), chamada no evento `startup` do FastAPI (`backend/app/main.py`): se `APP_ENV=production` e `AUTH_TOKEN_SECRET` estiver ausente ou for um dos valores considerados inseguros (`None`, vazio, `change-me`, `CHANGE_ME`, `replace-me`), a API falha ao subir (`RuntimeError`) em vez de servir tráfego assinando tokens com o segredo de desenvolvimento.

Essa validação é a última linha de defesa contra esse risco específico — não deve ser removida, enfraquecida ou contornada sem substituí-la por um controle equivalente (ex.: exigir `AUTH_TOKEN_SECRET` de um secret manager antes mesmo do container subir).

### Sessao do dashboard: cookie httpOnly (EPIC 17)

Desde a EPIC 17, o dashboard nao guarda mais o `access_token` em `localStorage`. O proxy interno `/api/backend` (`frontend/dashboard/app/api/backend/[...path]/route.ts`, server-side) passou a ser o unico ponto que conhece o token:

```text
Login (POST /api/v1/auth/login): o proxy recebe access_token/expires_in do backend, seta o cookie itcenter_session (httpOnly, Secure quando HTTPS real via X-Forwarded-Proto, SameSite=Strict, path=/, maxAge=expires_in) e devolve ao browser apenas { user }, sem o token no corpo.
Demais chamadas: o proxy le o cookie itcenter_session e monta o header Authorization: Bearer <token> antes de repassar ao backend. O client nunca mais monta esse header.
Logout (POST /api/v1/auth/logout): o proxy sempre expira o cookie (maxAge=0), mesmo se a chamada ao backend falhar.
```

O contrato do backend (ADR-022) nao muda: `POST /api/v1/auth/login` continua devolvendo `access_token`/`token_type`/`expires_in`/`user` no JSON. A migracao para cookie e inteiramente uma decisao de armazenamento no Next.js — o backend continua emitindo Bearer token HMAC SHA-256 e nao sabe nem precisa saber que o Next.js guarda esse token em cookie.

Motivo original (risco corrigido):

* Token em `localStorage` e acessivel a qualquer script executando na pagina; se um vetor de XSS surgisse no futuro, o token poderia ser lido e exfiltrado por JavaScript. Cookie `httpOnly` elimina esse vetor especifico.
* O frontend nao usa `dangerouslySetInnerHTML`, `eval` ou HTML nao sanitizado em nenhum componente (confirmado por revisao completa em 2026-07-29), o que ja reduzia a chance de um XSS aparecer — mas o cookie `httpOnly` remove a dependencia dessa garantia.

Gate complementar: `frontend/dashboard/middleware.ts` bloqueia o acesso as paginas protegidas (incluindo `/executive`, desde a EPIC 26) quando o cookie `itcenter_session` esta ausente, redirecionando para `/login` no edge (checagem de presenca, nao de validade — a validade continua sendo checada em `/api/v1/auth/me`, agora via `AuthProvider` em `app/(authenticated)/layout.tsx`, buscado uma unica vez por sessao em vez de a cada pagina — ver EPIC 26 em `docs/development/TASKS.md`).

## Auditoria

Tabela:

```text
audit_logs
```

Campos minimos:

| Campo | Tipo Conceitual | Obrigatorio | Observacao |
| --- | --- | --- | --- |
| `id` | integer/uuid | sim | Identificador interno. |
| `actor_user_id` | integer/uuid nullable | nao | Usuario responsavel; nulo para evento de sistema. |
| `action` | string | sim | Acao executada. |
| `entity_type` | string | sim | Tipo da entidade afetada. |
| `entity_id` | string/integer nullable | nao | Identificador da entidade afetada. |
| `ip_address` | string nullable | nao | IP de origem quando disponivel; confiabilidade limitada, ver ressalva abaixo. |
| `user_agent` | string nullable | nao | User-Agent quando disponivel. |
| `metadata` | json | sim | Dados adicionais sem segredo. |
| `created_at` | timestamp | sim | Data da acao. |

Nota sobre `ip_address` (corrigido na EPIC 28, 2026-08-17): `request_ip()` (`backend/app/services/auth.py`) le `X-Real-IP` — definido pelo proprio Nginx como `$remote_addr` em todos os `location` de `infra/nginx/nginx.conf.template`, nao anexavel/forjavel pelo cliente — em vez do primeiro valor de `X-Forwarded-For` (que usa `$proxy_add_x_forwarded_for`, que ANEXA o IP real ao valor ja enviado pelo cliente em vez de sobrescreve-lo, permitindo forjar o primeiro valor da lista). Fallback para `request.client.host` quando `X-Real-IP` nao vier, preservando o suporte a rodar sem Nginx na frente (dev/testes). `audit_logs` (`auth.login`, `auth.login_failed`, `alert.resolve`, `machine.rustdesk_update`) passam a gravar esse IP nao forjavel.

Invariantes:

* `actor_user_id` referencia `users(id)` quando houver usuario humano autenticado.
* `actor_user_id` pode ser nulo para eventos de sistema.
* `action` e `entity_type` sao obrigatorios e nao podem ser vazios.
* `metadata` usa JSONB com default `{}`.
* `metadata` nao deve armazenar senha, token, API Key ou segredo.

Acoes auditaveis minimas:

* login;
* logout;
* falha de login;
* criacao de usuario;
* alteracao de papel;
* desativacao de usuario;
* resolucao de alerta;
* alteracao de configuracao administrativa;
* alteracao de politica SOC.

## Regra 1 do SOC (`failed_login`) x falha de login do dashboard

Não confundir os dois eventos, apesar do nome parecido:

* A Regra 1 de `SOC_RULES.md` (evento `failed_login`) mede falhas de **logon local do Windows**, reportadas pelo agente no campo `security.failed_logins_last_hour` do payload de check-in (ver `docs/agent/CHECKIN.md`) — é sobre a máquina monitorada, não sobre o dashboard.
* A auditoria `auth.login_failed` (tabela `audit_logs`, listada acima) registra tentativas malsucedidas de login **no dashboard** (`POST /api/v1/auth/login`), mas hoje é apenas um registro de auditoria — não existe regra SOC, alerta ou telemetria de brute-force olhando para esse evento.

Ou seja: hoje não existe alerta cobrindo múltiplas tentativas de login incorretas contra `/api/v1/auth/login` — apenas o log de auditoria. Ver risco aceito relacionado em `docs/security/SECURITY.md` (seção "OWASP Top 10 — Controles Reais Aplicados").

## Rotas Protegidas

Todas as rotas administrativas exigem autenticacao de usuario humano.

Exemplos:

```text
GET /api/v1/machines
GET /api/v1/machines/{id}
GET /api/v1/machines/{id}/metrics
GET /api/v1/machines/{id}/programs
GET /api/v1/machines/{id}/admins
PATCH /api/v1/machines/{id}/rustdesk
GET /api/v1/alerts
PATCH /api/v1/alerts/{id}/resolve
GET /api/v1/security-events
GET /api/v1/dashboard/summary
GET /api/v1/reports/executive.pdf
GET /api/v1/machines/{id}/report.pdf
```

`PATCH /api/v1/machines/{id}/rustdesk` (EPIC 19, ADR-027) segue o mesmo padrão de `PATCH /api/v1/alerts/{id}/resolve`: exige `admin` ou `analyst` (`viewer` recebe `403`) e registra `audit_logs` com `action = "machine.rustdesk_update"`. O dashboard (`MachineDetailView.tsx`) reflete o mesmo RBAC no cliente: o formulário de cadastro e o botão "Conectar" ficam desabilitados para `viewer` (o botão "Conectar" só é renderizado como link ativo quando o papel permite; para `viewer`, aparece desabilitado com `title` explicativo) — a aplicação da regra em si continua sendo do backend, o frontend só evita expor a ação de forma confusa.

`GET /api/v1/dashboard/summary`, `GET /api/v1/reports/executive.pdf` e `GET /api/v1/machines/{id}/report.pdf` (EPIC 20, ADR-029) seguem o mesmo RBAC de leitura das telas já existentes: `admin`, `analyst` e `viewer` podem acessar (nenhum papel é bloqueado, pois são apenas leitura/exportação de dados já visíveis nas telas atuais).

Excecoes previstas:

```text
GET /api/v1/health
POST /api/v1/agent/checkin
GET /api/v1/agent/manifest
GET /api/v1/agent/download
```

`POST /api/v1/agent/checkin`, `GET /api/v1/agent/manifest` e `GET /api/v1/agent/download` (EPIC 22, ADR-032) devem continuar protegidos por `X-Agent-Api-Key`, nao por login humano — sao autenticacao de classe do agente, nao identidade individual (o `agent_secret` do ADR-036 e especifico do check-in, `manifest`/`download` nao carregam dado por maquina alem do `target_agent_version` opcional via query `hostname`). `infra/nginx/nginx.conf.template` isenta os 3 do Basic Auth — a isencao de `manifest`/`download` foi corrigida em 2026-08-19 (EPIC 37, blocos `location =` dedicados), validada localmente ponta a ponta contra o backend real. **Ainda nao deployado em `itcenter-edge-01`** (ver `docs/deployment/KNOWN_ISSUES.md`) — ate o proximo deploy de producao, a VM real continua sem essa isencao para `manifest`/`download`.

## API Key por Agente

Estado atual:

```text
AGENT_API_KEY unica por ambiente.
```

### Personificacao de maquina — corrigido em 2026-08-17 (ADR-036, EPIC 28-A)

Ate 2026-08-17 este era um risco concreto ja explorável, nao so uma melhoria futura: o backend validava somente a `AGENT_API_KEY` global e identificava a maquina exclusivamente pelo `hostname` autorreportado, sem vinculo servidor-side entre a chave usada e uma maquina especifica.

Corrigido com um segredo por maquina em modelo trust-on-first-use: no primeiro check-in de um hostname novo (ou de um hostname ja cadastrado que ainda nao tinha segredo — janela de transicao unica, ver ADR-036), o backend gera um segredo aleatorio de 256 bits, devolve-o em texto puro so nessa resposta (`AgentCheckinResponse.agent_secret`), e passa a exigi-lo (comparado so pelo hash SHA-256, `machines.agent_secret_hash`) em todo check-in seguinte daquele hostname. Um check-in sem o segredo certo e rejeitado com 401 — **sem sobrescrever nenhum dado da maquina** — e gera o evento/alerta SOC `machine_identity_mismatch` (severidade alta, ver `docs/security/SOC_RULES.md`). O agente Windows (`itcenter-agent.ps1`) persiste o segredo recebido em `config.json` (mesma ACL restrita do ADR-025) e o reenvia em todo check-in futuro. Testado: `pytest` (98 passed, incluindo 5 casos novos de identidade) e `run-agent-tests.ps1`.

`AGENT_API_KEY` continua existindo como primeira camada (autenticacao do agente como classe); o segredo por maquina e a segunda camada (identidade da maquina individual dentro dessa classe) — nao sao a mesma coisa nem um substitui o outro.

Planejamento futuro (evolucao completa do modelo de credencial, alem da correcao acima):

* Criar tabela propria para credenciais de agentes.
* Gerar uma chave por maquina/agente.
* Armazenar apenas hash da API Key.
* Permitir rotacao e revogacao por agente.
* Registrar ultimo uso da chave.
* Manter `X-Agent-Api-Key` como header de transporte.
* Nao misturar credenciais de agente com usuarios humanos da tabela `users`.

## Fora do escopo atual

Ainda nao existe:

* CRUD administrativo de usuarios;
* revogacao server-side de token antes da expiracao;
* API Key individual por agente;
* auditoria de todas as acoes futuras ainda nao implementadas;
* rate limit ou lockout de conta apos multiplas falhas de login humano em `POST /api/v1/auth/login` — nem o Nginx (so existe `limit_req_zone` para a zona `agent_checkins`, `infra/nginx/nginx.conf.template`) nem a aplicacao aplicam esse controle hoje; risco aceito conhecido, detalhado em `docs/security/SECURITY.md`;
* politica minima de senha (comprimento, complexidade) na criacao de usuario — `backend/create_admin.py` exige apenas que `ADMIN_PASSWORD` nao seja vazio, sem validar comprimento ou complexidade.

Esses controles pertencem a proximas etapas de governanca.
