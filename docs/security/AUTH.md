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
* Erros de login sao genericos para nao enumerar usuarios.

### Risco conhecido: token guardado em localStorage no frontend

Auditoria de seguranca do frontend em 2026-07-29 (`frontend/dashboard/lib/api.ts`) confirmou que o dashboard guarda o `access_token` em `localStorage` do navegador, nao em cookie `httpOnly`.

Classificacao: **Alta** (ver EPIC 17 em `docs/development/TASKS.md`).

Motivo da prioridade:

* E o unico dado de sessao do usuario humano; se qualquer vetor de XSS surgir no futuro (hoje nao ha nenhum identificado no codigo atual), o token pode ser lido e exfiltrado por JavaScript.
* Cookie `httpOnly` eliminaria esse vetor especifico, pois o token deixaria de ser acessivel via `document`/`window` para script no navegador.

Mitigacao atual:

* O frontend nao usa `dangerouslySetInnerHTML`, `eval` ou HTML nao sanitizado em nenhum componente (confirmado por revisao completa em 2026-07-29), reduzindo a chance de um XSS aparecer.

Evolucao planejada:

* Migrar para cookie `httpOnly` + `Secure` + `SameSite=Strict`, setado pelo backend/BFF no login, com o proxy `/api/backend` lendo o cookie em vez de exigir `Authorization` manual do client. Isso exige revisar o contrato de `ADR-022` antes de implementar.

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
| `ip_address` | string nullable | nao | IP de origem quando disponivel. |
| `user_agent` | string nullable | nao | User-Agent quando disponivel. |
| `metadata` | json | sim | Dados adicionais sem segredo. |
| `created_at` | timestamp | sim | Data da acao. |

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

## Rotas Protegidas

Todas as rotas administrativas exigem autenticacao de usuario humano.

Exemplos:

```text
GET /api/v1/machines
GET /api/v1/machines/{id}
GET /api/v1/machines/{id}/metrics
GET /api/v1/machines/{id}/programs
GET /api/v1/machines/{id}/admins
GET /api/v1/alerts
PATCH /api/v1/alerts/{id}/resolve
GET /api/v1/security-events
```

Excecoes previstas:

```text
GET /health
POST /api/v1/agent/checkin
```

`POST /api/v1/agent/checkin` deve continuar protegido por `X-Agent-Api-Key`, nao por login humano.

## API Key por Agente

Estado atual:

```text
AGENT_API_KEY unica por ambiente.
```

Planejamento futuro:

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
* auditoria de todas as acoes futuras ainda nao implementadas.

Esses controles pertencem a proximas etapas de governanca.
